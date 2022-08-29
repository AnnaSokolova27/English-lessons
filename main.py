import dash
from dash import dcc
from dash import html

from textdistance import levenshtein as lev

import re

import spacy
import pymorphy2

import base64
import os
from io import BytesIO


import pytesseract
import cv2

from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

from googletrans import Translator

from PIL import Image

app = dash.Dash(title="English lessons", suppress_callback_exceptions=True)
#server = app.server()
colors = {
   'background': '#FFE4C4'
}

pytesseract.pytesseract.tesseract_cmd = r'C:/Program Files/Tesseract-OCR/tesseract.exe'
nlp = spacy.load("en_core_web_lg")
nlp2 = spacy.load("ru_core_news_sm")
morph = pymorphy2.MorphAnalyzer()
idioms = ["by the skin of your teeth", "cry wolf", "play the devil's advocate", "up in the air", "A blessing in disguise", "Drive you up the wall" ]
translations = ["еле-еле", "бить ложную тревогу", "спорить ради обсуждения", "в подвешанном состоянии", "к лучшему", "раздражать"]
min_score = [5, 3, 3, 2, 2, 7]

tab_selected_style = {
    'border-top': '2px solid #a0a0a0',
    'border-left': '1px solid #a0a0a0',
    'border-right': '1px solid #a0a0a0',
    'padding': '6px',
    'color': '#FF6699',
    'font-weight': 'bold'
}

TAB1 = [
   html.H1(children=[
      html.Button(dcc.Link('Learn', href='/learnIdioms'), id='learnIdioms', className='ControlButton', n_clicks=0),
      html.Button(dcc.Link('Test', href='/testIdioms'), id='testIdioms', className='ControlButton', n_clicks=0, draggable='True'),
      html.Br(),
      html.Button(dcc.Link('Translator', href='/translator'), id='learnIdioms', className='ControlButton', n_clicks=0)],
   ),
]
TAB2 = [
   html.H1(children=[
      html.Button(dcc.Link('Learn', href='/learnPhV'), id='learnPhv', className='ControlButton', n_clicks=0),
      html.Button(dcc.Link('Test', href='/testPhV'), id='testPhV', className='ControlButton', n_clicks=0),
      html.Br(),
      html.Button(dcc.Link('Translator', href='/translator'), id='learnIdioms', className='ControlButton', n_clicks=0)],
   ),
]

TAB3 = [
   html.H1(children=[
      html.Button(dcc.Link('Learn', href='/learnVoc'), id='learnVoc', className='ControlButton', n_clicks=0),
      html.Button(dcc.Link('Test', href='/testVoc'), id='testVoc', className='ControlButton', n_clicks=0),
      html.Br(),
      html.Button(dcc.Link('Translator', href='/translator'), id='learnIdioms', className='ControlButton', n_clicks=0)],
   ),
]


app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

index_page = html.Div(style={'background-color': colors['background']}, children=[
   html.H1('Welcome!'),
   html.H2('Choose what you want to learn:'),
   html.Div([
       dcc.Tabs(
            id='tabs',
            className='Tab',
            persistence= True,
            children=[
                dcc.Tab(
                    id='tab1',
                    label='Idioms',
                    children=TAB1,
                    selected_style=tab_selected_style
                ),

                dcc.Tab(
                    id='tab2',
                    label='Phrasal verbs',
                    children=TAB2,
                    selected_style=tab_selected_style
                ),

                dcc.Tab(
                    id='tab3',
                    label='Vocabulary',
                    children=TAB3,
                    selected_style=tab_selected_style
                ),
            ],
       ),
   ]),
],
)

translator_layout = html.Div(style={'background-color': colors['background'], 'overflow-x': 'scroll'}, children=[
    html.H1('Write what do you want to translate:'),
    dcc.Textarea(
            id='translator_input',
            spellCheck=False,
            value='',
            name='text',
    ),
    html.Br(),
    html.Br(),
    html.Button('Translate', id='textarea-state-example-button', n_clicks=0),
    html.Br(),
    html.Br(),
    html.Div(id='translator_output'),
    dcc.Upload(
        id='upload-image',
        children=html.Div([
            html.A('Upload photo for translation')
        ]),
        multiple=True
    ),
    html.Div(id='output-image-upload'),
    html.Br(),
    html.Br(),
    dcc.Link('Home page', className='Link', href='/'),
])

def translatorr(txt_inserted):
    txt_inserted = txt_inserted.lower()
    translator = Translator()
    if ((txt_inserted == '') or (txt_inserted.isspace())):
        return txt_inserted
    else:
        split_regex = re.compile(r'[.|!|?|…]')
        sentences = filter(lambda t: t, [t.strip() for t in split_regex.split(txt_inserted)])
        for sentence in sentences:
            tokens = sentence.split(' ')
            n = 0
            for phrase in idioms:
                score = 1000
                subseq = ''
                for i in range(len(tokens)):
                    if len(tokens) - i < 5:
                        k = len(tokens) - i
                    else:
                        k = 6
                    for j in range(i, i + k + 1):
                        subseqNew = ' '.join(tokens[i:j])
                        distance = lev.distance(phrase, subseqNew)
                        if distance < score:
                            score = distance
                            subseq = subseqNew
                if score <= min_score[n]:
                    sentenceNew = sentence
                    time = ''
                    textAnalisSen = nlp(sentence)
                    for word in textAnalisSen:
                        wordPosition = 1
                        if word.dep_ == 'nsubj' or word.dep_ == 'nsubjpass':
                            russianWord = translator.translate(word.text, src='en', dest='ru').text
                            gender = morph.parse(russianWord)[0].tag.gender
                            number = morph.parse(russianWord)[0].tag.number
                        elif word.dep_ == 'aux':
                            time = word.tag_
                            if time == 'MD' and word.text == 'will':
                                if number == 'sing':
                                    sentenceNew = sentenceNew.replace(textAnalisSen[wordPosition].text, 'будет')
                                else:
                                    sentenceNew = sentenceNew.replace(textAnalisSen[wordPosition].text, 'будут')
                            elif word.text != 'should' and word.text != 'must' and word.text != 'might' \
                                    and word.text != 'can' and word.text != 'could' and word.text != 'would'\
                                    and word.text != 'need' and word.text != 'let':
                                sentenceNew = sentenceNew.replace(textAnalisSen[wordPosition].text, '')
                        wordPosition = wordPosition + 1
                    translation = translations[n]
                    textAnalisSub = nlp(subseq)
                    for word1 in textAnalisSub:
                        if word1.pos_ == 'VERB':
                            tagVERB = word1.tag_
                            textAnalisTrans = nlp2(translation)
                            for word2 in textAnalisTrans:
                                if word2.pos_ == 'VERB':
                                    if tagVERB == 'VBD' or tagVERB == 'VBN'  or time == 'VBD' or time == 'VBN':
                                        wordChanged = morph.parse(word2.text)[0]
                                        if number == 'sing':
                                            if gender == 'femn':
                                                wordChanged = wordChanged.inflect({'past', 'femn'}).word
                                                translation = translation.replace(word2.text, wordChanged)
                                            else:
                                                wordChanged = wordChanged.inflect({'past', 'masc'}).word
                                                translation = translation.replace(word2.text, wordChanged)
                                        else:
                                            wordChanged = wordChanged.inflect({'past', 'plur'}).word
                                            translation = translation.replace(word2.text, wordChanged)

                    sentenceNew = sentenceNew.replace(subseq, translation)
                    txt_inserted = txt_inserted.replace(sentence, sentenceNew)
                n = n+1
        result = translator.translate(txt_inserted, src='en', dest='ru')
        return result.text

def parse_contents(contents: str, filename):
    b64_str = contents[contents.find(",")+1:]
    img = Image.open(BytesIO(base64.b64decode(b64_str)))
    txt_inserted = pytesseract.image_to_string(img)
    result = translatorr(txt_inserted)
    return html.Div(
        [
            html.H5(filename),
            html.Img(src=contents),
            html.Br(),
            html.H4("Текст на фото: "),
            html.H4(txt_inserted),
            html.Br(),
            html.H4("Перевод: "),
            html.H4(result),
            html.Hr(),
            ]
    )

@app.callback(Output('output-image-upload', 'children'),
              Input('upload-image', 'contents'),
              Input('upload-image', 'filename'))
def update_output(list_of_contents, list_of_names):
    if list_of_contents is not None:
        children = [
            parse_contents(c, n) for c, n in
            zip(list_of_contents, list_of_names)]
        return children

@app.callback(
    Output(component_id='translator_output', component_property='children'),
    Input(component_id='translator_input', component_property='value'),
)
def simple_translate(txt_inserted):
    return translatorr(txt_inserted)



learnIdioms_layout = html.Div(style={'background-color': colors['background']}, children=[
    html.H1('Idioms'),
    html.Br(),
    html.H3("1) Beat around the bush = speak indirectly without getting to the main point. (Ходить вокруг да около)."),
    html.Br(),
    html.H4("Example: Stop beating around the bush and tell me: do you want to go with me or not?"),
    html.Br(), html.Br(),
    html.Audio(src=app.get_asset_url("sounds/beat.mp3"), id='audio', autoPlay=False, controls=True),
    html.Br(),
    html.Img(className='Image', src=app.get_asset_url("images/beatAround.jpg"), height=500, width=500),
    html.Br(),
    html.Video(src=app.get_asset_url("sounds/beatAround.mp4"), id='video', autoPlay=False, controls=True),
    html.Br(),
    html.H3("2) Tip of the iceberg = small part of something bigger, usually negative. (Маленькая часть чего-либо)."),
    html.Br(),
    html.H4("Example: When a person lies in small details, this is probably just the tip of the iceberg."),
    html.Br(), html.Br(),
    html.Img(className='Image', src=app.get_asset_url("images/iceberg.jpg"), height=500, width=500),
    html.Br(),
    html.Video(src=app.get_asset_url("sounds/beatAround.mp4"), id='video', autoPlay=False, controls=True),
    html.Br(),
    html.H3("3)	Nip something in the bud = stop a bad situation from becoming worse by taking quick action. (Предотвратить что-то в самом начале)."),
    html.Br(),
    html.H3("Example: When my son first lied to me, I knew that I needed to nip it in the bud."),
    html.Br(), html.Br(),
    html.Img(className='Image', src=app.get_asset_url("images/nipIt.jpg"), height=500, width=500),
    html.Br(),
    html.Video(src=app.get_asset_url("sounds/nipIt.mp4"), id='video', autoPlay=False, controls=True),
    html.Br(),
    html.H3("4)	Cry wolf = to lie many times so no one believes you. (Врать много раз, после чего люди перестают тебе верить)."),
    html.Br(),
    html.H3("Example: Weather forecasters cry wolf about dangerous hurricanes so many times that people stop believing them."),
    html.Br(), html.Br(),
    html.Audio(src=app.get_asset_url("sounds/cryingWolf.mp3"), id='audio', autoPlay=False, controls=True),
    html.Br(),
    html.Img(className='Image', src=app.get_asset_url("images/cryWolf.jpg"), height=500, width=500),
    html.Br(),
    html.Video(src=app.get_asset_url("sounds/cryWolf.mp4"), id='video', autoPlay=False, controls=True),
    html.Br(),
    html.H3("5)	Rule of thumb = a general rule or guideline. (Основное/негласное правило)."),
    html.Br(),
    html.H3("Example: Texting your friend before you go to his house is a good rule of thumb."),
    html.Br(), html.Br(),
    html.Img(className='Image', src=app.get_asset_url("images/thumb.jpg"), height=500, width=500),
    html.Br(),
    html.Video(src=app.get_asset_url("sounds/thumb.mp4"), id='video', autoPlay=False, controls=True),
    html.Br(),
    html.H3("6)	Play the devil's advocate = to argue the opposite opinion for the purpose of debate. (Спорить ради обсуждения)."),
    html.Br(),
    html.H3("Example: To play the devil's advocate, aren't e-books  more convenient that paper books?"),
    html.Br(), html.Br(),
    html.Img(className='Image', src=app.get_asset_url("images/advocate.jpg"), height=500, width=500),
    html.Br(),
    html.Video(src=app.get_asset_url("sounds/advocate.mp4"), id='video', autoPlay=False, controls=True),
    html.Br(),
    html.H3("7)	Easier said than done = not as easy as it seems. (Не так просто, как кажется)."),
    html.Br(),
    html.H3("Example: It’s better to use English every day when you learn it, but easier said than done."),
    html.Br(), html.Br(),
    html.Img(className='Image', src=app.get_asset_url("images/easier.jpg"), height=500, width=500),
    html.Br(),
    html.Video(src=app.get_asset_url("sounds/easier.mp4"), id='video', autoPlay=False, controls=True),
    html.Br(),
    html.H3("8)	By the skin of someone’s teeth = to just barely make it. (Сделать с трудом, еле-еле)."),
    html.Br(),
    html.H3("Example: You passed your exam by the skin of your teeth."),
    html.Br(), html.Br(),
    html.Img(className='Image', src=app.get_asset_url("images/teeth.jpg"), height=500, width=500),
    html.Br(),
    html.Video(src=app.get_asset_url("sounds/teeth.mp4"), id='video', autoPlay=False, controls=True),
    html.Br(),
    html.H3("9)	Up in the air = no definite plans. (Неопределённые/неточные планы)."),
    html.Br(),
    html.H3("Example: I want to visit Switzeland next year, but our travel plans are up in the air."),
    html.Br(), html.Br(),
    html.Img(className='Image', src=app.get_asset_url("images/air.jpg"), height=500, width=500),
    html.Br(),
    html.Video(src=app.get_asset_url("sounds/air.mp4"), id='video', autoPlay=False, controls=True),
    html.Br(),
    html.H3("10) Spill the beans = to tell a secret. (Рассказывать секрет)."),
    html.Br(),
    html.H3("Example: Don’t spill the beans until I’m ready to tell everyone!"),
    html.Br(), html.Br(),
    html.Img(className='Image', src=app.get_asset_url("images/beans.jpg"), height=500, width=500),
    html.Br(),
    html.Video(src=app.get_asset_url("sounds/beans.mp4"), id='video', autoPlay=False, controls=True),
    html.Br(),
    html.H3("11) Drive someone up the wall = to make someone mad, angry crazy. (Раздражать, злить кого-то). "),
    html.Br(),
    html.H3("Example: My dog’s constant barking is driving me up the wall."),
    html.Br(), html.Br(),
    html.Img(className='Image', src=app.get_asset_url("images/wall.jpg"), height=500, width=500),
    html.Br(),
    html.H3("12) A blessing in disguise = a bad situation that turned out to have an unexpectedly good outcome. (Плохая ситуация, которая привела к неожиданно хорошему исходу, к лучшему)."),
    html.Br(),
    html.H3("Example: She got fired from her job but it was a blessing in disguise because she found a better job then."),
    html.Br(), html.Br(),
    html.Img(className='Image', src=app.get_asset_url("images/blessing.jpg"), height=500, width=500),
    html.Br(),
    dcc.Link('Home page', className='Link', href='/'),
])

learnPhV_layout = html.Div(style={'background-color': colors['background']}, children=[
    html.H1('Phrasal verbs'),
    html.Br(),
    html.H3("1)	To get around (to it) = to delay doing something. (Отложить дело)."),
    html.Br(),
    html.H4("Example: I’ll get around to cleaning the room later."),
    html.Br(), html.Br(),
    html.Img(className='Image', src=app.get_asset_url("images/getAround.jpg"), height=300, width=500),
    html.Br(),
    html.Video(src=app.get_asset_url("sounds/getAround.mp4"), id='video', autoPlay=False, controls=True),
    html.Br(),
    html.H3("2)	To come down with = to become sick. (Заболеть чем-либо)."),
    html.Br(),
    html.H4("Example: I think I’m coming down with the flu."),
    html.Br(), html.Br(),
    html.Img(className='Image', src=app.get_asset_url("images/comeDown.jpg"), height=500, width=500),
    html.Br(),
    html.Video(src=app.get_asset_url("sounds/comeDown.mp4"), id='video', autoPlay=False, controls=True),
    html.Br(),
    html.H3("3)	To cut back on = to consume less of something. (Употреблять меньше чего-либо)."),
    html.Br(),
    html.H3("Example: I’m trying to cut back on fried food, but it’s so tasty!"),
    html.Br(), html.Br(),
    html.Img(className='Image', src=app.get_asset_url("images/cutBack.jpg"), height=500, width=800),
    html.Br(),
    html.Video(src=app.get_asset_url("sounds/cutBack.mp4"), id='video', autoPlay=False, controls=True),
    html.Br(),
    html.H3("4)	To end up = to eventually decide or reach something. (В конце концов решить что-либо сделать)."),
    html.Br(),
    html.H3("Example: We ended up just ordering pizza and not going to the fancy restaurant."),
    html.Br(), html.Br(),
    html.Img(className='Image', src=app.get_asset_url("images/endUp.jpg"), height=500, width=800),
    html.Br(),
    html.Video(src=app.get_asset_url("sounds/endUp.mp4"), id='video', autoPlay=False, controls=True),
    html.Br(),
    html.H3("5)	To fill out = to write information on a form. (Заполнить анкету/форму)."),
    html.Br(),
    html.H3("Example: Can you please fill out these forms?"),
    html.Br(), html.Br(),
    html.Img(className='Image', src=app.get_asset_url("images/fillOut.jpg"), height=500, width=800),
    html.Br(),
    html.Video(src=app.get_asset_url("sounds/fillOut.mp4"), id='video', autoPlay=False, controls=True),
    html.Br(),
    html.H3("6)	To bring up = to mention in conversation. (Упоминать в разговоре)."),
    html.Br(),
    html.H3("Example: You shouldn't bring up politics in this house unless you're ready for a long discussion."),
    html.Br(), html.Br(),
    html.Img(className='Image', src=app.get_asset_url("images/bring-up.jpg"), height=500, width=800),
    html.Br(),
    html.Video(src=app.get_asset_url("sounds/bringUp.mp4"), id='video', autoPlay=False, controls=True),
    html.Br(),
    html.H3("7)	To put up with = to tolerate something or someone. (Терпеть кого-то, смириться с чем-то)."),
    html.Br(),
    html.H3("Example: I don’t know how he puts up with deceptions."),
    html.Br(), html.Br(),
    html.Img(className='Image', src=app.get_asset_url("images/putUp.jpg"), height=500, width=800),
    html.Br(),
    html.Video(src=app.get_asset_url("sounds/putUp.mp4"), id='video', autoPlay=False, controls=True),
    html.Br(),
    html.H3("8)	To warm up to = to start liking someone or something. (Начать любить, свыкнуться)."),
    html.Br(),
    html.H3("Example: It took my cat a while to warm up to me."),
    html.Br(), html.Br(),
    html.Img(className='Image', src=app.get_asset_url("images/warmUp.jpg"), height=500, width=800),
    html.Br(),
    html.Video(src=app.get_asset_url("sounds/warmUp.mp4"), id='video', autoPlay=False, controls=True),
    html.Br(),
    html.H3("9)	To wear off = to fade away. (Исчезнуть, закончиться)."),
    html.Br(),
    html.H3("Example: My energy starts to wear off around noon."),
    html.Br(), html.Br(),
    html.Img(className='Image', src=app.get_asset_url("images/wearOff.jpg"), height=500, width=800),
    html.Br(),
    html.Video(src=app.get_asset_url("sounds/wearOff.mp4"), id='video', autoPlay=False, controls=True),
    html.Br(),
    html.H3("10)To chip in = to help or contribute money or energy. (Скидываться, помогать)."),
    html.Br(),
    html.H3("Example: I couldn't go to the party, but I still wanted to chip in for a gift."),
    html.Br(), html.Br(),
    html.Img(className='Image', src=app.get_asset_url("images/chipIn.jpg"), height=500, width=800),
    html.Br(),
    html.Video(src=app.get_asset_url("sounds/chipIn.mp4"), id='video', autoPlay=False, controls=True),
    html.Br(),
    html.Br(), html.Br(),
    dcc.Link('Home page', className='Link', href='/'),
])

learnVoc_layout = html.Div(style={'background-color': colors['background']}, children=[
    html.H1('Vocabulary'),
    html.Br(),
    html.H3("1)	Captivating = capable of attracting and holding interest; charming. (Чарующий, завораживающий)."),
    html.Br(),
    html.H3("Example: Her eyes were so captivating."),
    html.Br(),
    html.Video(src=app.get_asset_url("sounds/captivating.mp4"), id='video', autoPlay=False, controls=True),
    html.Br(),
    html.Br(), html.Br(),
    html.H3("2)	Dormant = a state of rest or inactivity. (Неактивный, спящий)."),
    html.Br(),
    html.H3("Example: The seeds that were dormant during the winter grew into beautiful flowers in the spring."),
    html.Br(), html.Br(),
    html.H3("3)	Facilitate = to make an action or process easy. (Облегчать, содействовать)."),
    html.Br(),
    html.H3("Example: Technology has been used to facilitate working from home."),
    html.Br(), html.Br(),
    html.H3("4)	Immersion = being completely surrounded by something. (Погружение)."),
    html.Br(),
    html.H3("Example: One great way to practice language immersion is to watch movies and TV shows in the language you want to learn."),
    html.Br(), html.Br(),
    html.H3("5)	Deficiency = an amount that is lacking  or inadequate. (Недостаток, дефицит)."),
    html.Br(),
    html.H3("Example: Not eating enough fruits and vegetables can cause vitamin deficiency."),
    html.Br(), html.Br(),
    html.H3("6)	Intriguing = something that sparks curiosity. (Увлекательный, интригующий)."),
    html.Br(),
    html.H3("Example: The documentary about outer space was intriguing."),
    html.Br(), html.Br(),
    html.H3("7)	Phony = fake, shallow. (Фальшивый, лживый)."),
    html.Br(),
    html.H3("Example: We both dislike phony people"),
    html.Br(), html.Br(),
    html.H3("8)	Sustainable = able to continue over a period of time. (Устойчивый, долговременный)."),
    html.Br(),
    html.H3("Example: This started a very sustainable practice that has lasted hundreds of years."),
    html.Br(), html.Br(),
    html.H3("9)	Tackle = to try to deal with something or someone. (Заняться, решить)."),
    html.Br(),
    html.H3("Example: There are many ways of tackling this problem."),
    html.Br(), html.Br(),
    html.H3("Acknowledge = to take notice of. (Признавать, замечать)."),
    html.Br(),
    html.H3("Example: My cat won’t even acknowledge me unless I am holding a bag of treats."),
    html.Br(), html.Br(),
    dcc.Link('Home page', className='Link', href='/'),
])

testIdioms_layout = html.Div(style={'background-color': colors['background']}, children=[
    html.H1('Idioms'),
    html.H4('*Instruction: press "enter" to check each of your answers.*'),
    html.Br(), html.Br(), html.Br(),
    html.H3('1)Insert the missing word:'),
    html.Br(), html.Br(),
    html.Div([
        html.H4("Let's stop beating around the "),
        dcc.Input(
            id='my_txt_input',
            type='text',
            debounce=True,
            pattern=r"^[A-Za-z].*",
            spellCheck=False,
            inputMode='latin',
            name='text',
            autoFocus=False,
            autoComplete='off'
        ),
        html.Div(id='div_output'),
    ]),
    html.Br(), html.Br(), html.Br(),
    html.H3('2)Listen to the audio and complete the sentence:   '),
    html.Br(), html.Br(),
    html.H4('.... and tell me: do you want to date me or not?'),
    html.Div([
        html.Audio(src=app.get_asset_url("sounds/beatEx.mp3"), autoPlay=False, controls=True),
        dcc.Input(
            id='my_txt_input2',
            type='text',
            debounce=True,
            pattern=r"^[A-Za-z].*",
            spellCheck=True,
            inputMode='latin',
            name='text',
            autoFocus=False,
            autoComplete='off'
        ),
        html.Div(id='div_output2'),
    ]),
    html.Br(), html.Br(), html.Br(),
    html.H3('3)Translate the part of the sentence into English using one of the idiom:'),
    html.Br(), html.Br(),
    html.H4("Не рассказывай никому о том, что я вернулась в Москву, не выдавай секрет. - Don't tell anyone that I've returned to Moscow, dont'       "),
    dcc.Input(
            id='my_txt_input3',
            type='text',
            debounce=True,
            pattern=r"^[A-Za-z].*",
            spellCheck=True,
            inputMode='latin',
            name='text',
            autoFocus=False,
            autoComplete='off'
    ),
    html.Div(id='div_output3'),
    html.Br(), html.Br(), html.Br(),
    html.H3('4)Choose the correct translation for the sentence.'),
    html.Br(), html.Br(),
    html.H4('Джон сдал экзамен еле-еле. '),
    dcc.Dropdown(['John passed his exam effortlessly.', 'John passed his exam by the skin of his teeth.', 'John passed his exam up in the air.'], id='demo-dropdown', style={"width": "50%"}),
    html.Div(id='dropdown_output1'),
    html.Br(), html.Br(), html.Br(),
    html.H3('5)Read the text and translate all the idioms in it.'),
    html.Br(), html.Br(),
    html.H4("If you dream of adventures, you probably picture to yourself desert islands, wrecks of sunken ships and old chests filled with jewellery and coins. "
            "For some people these dreams have come true. It is because they really know where to look for treasure. What place are we talking about? "
            "Let's stop beating around the bush and start your tale. One of the best places for treasure hunting is the Atlantic Ocean near the eastern coast of Florida. "
            "This place is called “Treasure Coast” . Between the 16th and 18th century many Spanish ships sank near the coast and their wrecks were buried in the sand among the coral reefs. "
            "These ships sailed from Mexico to Spain and carried gold, silver and precious stones. They also transported Spanish soldiers and governors who were coming back home from the colonies with their own gold."
            " Most ships sank not very far from the coast. There was only one narrow channel, which ran between the massive and dangerous coral reefs. "
            "Besides, tropical storms or hurricanes were very common in late summer or early autumn and the ships often broke into pieces.The exploration of the sea near the coast has "
            "begun in the twentieth century when records of shipwrecks were found in the Spanish archives. First, there came scuba divers with metal detectors. "
            "Then, with the discovery of the first Spanish ship in the early 1970s, many people started treasure hunting. They were looking for anchors, captains’"
            " diaries and obviously for gold, silver and coins. Today, the treasure hunting is an expensive game, which requires professional equipment and expert divers. "
            "It is exhausting and quite dangerous.  It takes divers long hours to search for a ship under water but if they are lucky, they feel excited."),
    html.Br(), html.Br(), html.Br(),
    dcc.Link('Home page', className='Link', href='/')
])

def right_answer(text, task):
    text = str(text)
    text = text.lower()
    if (text == 'bush') and (task == 1):
        return "right", 'rightAnswer'
    elif (text == 'stop beating around the bush') and (task == 2):
        return "right", 'rightAnswer'
    elif (text == 'John passed his exam by the skin of his teeth.') and (task == 3):
        return "right", 'rightAnswer'
    elif (text == 'spill the beans') and (task == 4):
        return "right", 'rightAnswer'
    elif (text == 'coming down') and (task == 5):
        return "right", 'rightAnswer'
    elif (text == 'he puts up with deceptions') and (task == 6):
        return "right", 'rightAnswer'
    elif (text == 'We ended up just ordering pizza.') and (task == 7):
        return "right", 'rightAnswer'
    elif (text == 'cut back on') and (task == 8):
        return "right", 'rightAnswer'
    elif (text == 'tackling') and (task == 9):
        return "right", 'rightAnswer'
    elif (text == 'sustainable practice') and (task == 10):
        return "right", 'rightAnswer'
    elif (text == 'Not eating enough fruits and vegetables can cause vitamin deficiency.') and (task == 11):
        return "right", 'rightAnswer'
    elif (text == 'phony') and (task == 12):
        return "right", 'rightAnswer'
    else:
        return "wrong", 'wrongAnswer'

@app.callback(
    [Output(component_id='div_output', component_property='children'),
     Output(component_id='div_output', component_property='className')],
    [Input(component_id='my_txt_input', component_property='value'),
     Input(component_id='my_txt_input', component_property='n_submit')]
)
def update_answer(txt_inserted, n_submit):
    if n_submit is None:
        raise PreventUpdate
    else:
        return right_answer(txt_inserted, 1)

@app.callback(
    [Output(component_id='div_output2', component_property='children'),
     Output(component_id='div_output2', component_property='className')],
    [Input(component_id='my_txt_input2', component_property='value'),
     Input(component_id='my_txt_input2', component_property='n_submit')]
)
def update_answer(txt_inserted, n_submit):
    if n_submit is None:
        raise PreventUpdate
    else:
        return right_answer(txt_inserted, 2)

@app.callback(
    [Output(component_id='dropdown_output1', component_property='children'),
     Output(component_id='dropdown_output1', component_property='className')],
    Input('demo-dropdown', 'value')
)
def update_output(value):
    if value is None:
        raise PreventUpdate
    else:
        return right_answer(value, 3)

@app.callback(
    [Output(component_id='div_output3', component_property='children'),
     Output(component_id='div_output3', component_property='className')],
    [Input(component_id='my_txt_input3', component_property='value'),
     Input(component_id='my_txt_input3', component_property='n_submit')]
)
def update_answer(txt_inserted, n_submit):
    if n_submit is None:
        raise PreventUpdate
    else:
        return right_answer(txt_inserted, 4)

testPhV_layout = html.Div(style={'background-color': colors['background']}, children=[
    html.H1('Phrasal verbs'),
    html.H4('*Instruction: press "enter" to check each of your answers.*'),
    html.Br(), html.Br(), html.Br(),
    html.H3('1)Insert the missing word:'),
    html.Br(), html.Br(),
    html.Div([
        html.H4("I think I’m ...... with the flu. "),
        dcc.Input(
            id='inputPhV1',
            type='text',
            debounce=True,
            pattern=r"^[A-Za-z].*",
            spellCheck=False,
            inputMode='latin',
            name='text',
            autoFocus=False,
            autoComplete='off'
        ),
        html.Div(id='div_outputPhV1'),
    ]),
    html.Br(), html.Br(), html.Br(),
    html.H3('2)Listen to the audio and complete the sentence:   '),
    html.Br(), html.Br(),
    html.H4('I don’t know how ......'),
    html.Div([
        html.Audio(src=app.get_asset_url("sounds/beatEx.mp3"), autoPlay=False, controls=True),
        dcc.Input(
            id='inputPhV2',
            type='text',
            debounce=True,
            pattern=r"^[A-Za-z].*",
            spellCheck=True,
            inputMode='latin',
            name='text',
            autoFocus=False,
            autoComplete='off'
        ),
        html.Div(id='div_outputPhV2'),
    ]),
    html.Br(), html.Br(), html.Br(),
    html.H3('3)Translate the part of the sentence into English using one of the phrasal verbs:'),
    html.Br(), html.Br(),
    html.H4(
        "Я стараюсь употреблять меньше сладкого, но это так вкусно! - I’m trying to ..... sweet food, but it’s so tasty!"),
    dcc.Input(
        id='inputPhV3',
        type='text',
        debounce=True,
        pattern=r"^[A-Za-z].*",
        spellCheck=True,
        inputMode='latin',
        name='text',
        autoFocus=False,
        autoComplete='off'
    ),
    html.Div(id='div_outputPhV3'),
    html.Br(), html.Br(), html.Br(),
    html.H3('4)Choose the correct translation for the sentence.'),
    html.Br(), html.Br(),
    html.H4('В конце концов мы просто заказали пиццу. '),
    dcc.Dropdown(['We ended up just ordering pizza.', 'We decided just to order pizza.',
                  'We ended out just ordering pizza.'], id='demo-dropdown2', style={"width": "50%"}),
    html.Div(id='dropdown_output2'),
    html.Br(), html.Br(), html.Br(),
    html.H3('5)Read the text and translate all the phrasal phrasal verbs in it.'),
    html.Br(), html.Br(),
    html.Br(), html.Br(), html.Br(),
    dcc.Link('Home page', className='Link', href='/'),
])

@app.callback(
    [Output(component_id='div_outputPhV1', component_property='children'),
     Output(component_id='div_outputPhV1', component_property='className')],
    [Input(component_id='inputPhV1', component_property='value'),
     Input(component_id='inputPhV1', component_property='n_submit')]
)
def update_answer(txt_inserted, n_submit):
    if n_submit is None:
        raise PreventUpdate
    else:
        return right_answer(txt_inserted, 5)

@app.callback(
    [Output(component_id='div_outputPhV2', component_property='children'),
     Output(component_id='div_outputPhV2', component_property='className')],
    [Input(component_id='inputPhV2', component_property='value'),
     Input(component_id='inputPhV2', component_property='n_submit')]
)
def update_answer(txt_inserted, n_submit):
    if n_submit is None:
        raise PreventUpdate
    else:
        return right_answer(txt_inserted, 6)

@app.callback(
    [Output(component_id='dropdown_output2', component_property='children'),
     Output(component_id='dropdown_output2', component_property='className')],
    Input('demo-dropdown', 'value')
)
def update_output(value):
    if value is None:
        raise PreventUpdate
    else:
        return right_answer(value, 7)

@app.callback(
    [Output(component_id='div_outputPhV3', component_property='children'),
     Output(component_id='div_outputPhV3', component_property='className')],
    [Input(component_id='inputPhV3', component_property='value'),
     Input(component_id='inputPhV3', component_property='n_submit')]
)
def update_answer(txt_inserted, n_submit):
    if n_submit is None:
        raise PreventUpdate
    else:
        return right_answer(txt_inserted, 8)

testVoc_layout = html.Div(style={'background-color': colors['background']}, children=[
    html.H1('Vocabulary'),
    html.H4('*Instruction: press "enter" to check each of your answers.*'),
    html.Br(), html.Br(), html.Br(),
    html.H3('1)Insert the missing word:'),
    html.Br(), html.Br(),
    html.Div([
        html.H4("There are many ways of .... this problem. "),
        dcc.Input(
            id='inputVoc1',
            type='text',
            debounce=True,
            pattern=r"^[A-Za-z].*",
            spellCheck=False,
            inputMode='latin',
            name='text',
            autoFocus=False,
            autoComplete='off'
        ),
        html.Div(id='div_outputVoc1'),
    ]),
    html.Br(), html.Br(), html.Br(),
    html.H3('2)Listen to the audio and complete the sentence:   '),
    html.Br(), html.Br(),
    html.H4('This started a very ..... that has lasted hundreds of years'),
    html.Div([
        html.Audio(src=app.get_asset_url("sounds/beatEx.mp3"), autoPlay=False, controls=True),
        dcc.Input(
            id='inputVoc2',
            type='text',
            debounce=True,
            pattern=r"^[A-Za-z].*",
            spellCheck=True,
            inputMode='latin',
            name='text',
            autoFocus=False,
            autoComplete='off'
        ),
        html.Div(id='div_outputVoc2'),
    ]),
    html.Br(), html.Br(), html.Br(),
    html.H3('3)Translate the part of the sentence into English using one word:'),
    html.Br(), html.Br(),
    html.H4(
        "Нам обоим не нравятся лживые люди. - We both dislike ... people."),
    dcc.Input(
        id='inputVoc3',
        type='text',
        debounce=True,
        pattern=r"^[A-Za-z].*",
        spellCheck=True,
        inputMode='latin',
        name='text',
        autoFocus=False,
        autoComplete='off'
    ),
    html.Div(id='div_outputVoc3'),
    html.Br(), html.Br(), html.Br(),
    html.H3('4)Choose the correct translation for the sentence.'),
    html.Br(), html.Br(),
    html.H4('Недостаточное употребление витаминов может привести к дефициту витаминов . '),
    dcc.Dropdown(['Not eating enough fruits and vegetables can cause vitamin overabundance.', 'Not eating enough fruits and vegetables can cause vitamin surplus.',
                  'Not eating enough fruits and vegetables can cause vitamin deficiency.'], id='demo-dropdown3', style={"width": "50%"}),
    html.Div(id='dropdown_output3'),
    html.Br(), html.Br(), html.Br(),
    html.H3('5)Read the text and translate it.'),
    html.Br(), html.Br(),
    html.Br(), html.Br(), html.Br(),
    dcc.Link('Home page', className='Link', href='/'),
])

@app.callback(
    [Output(component_id='div_outputVoc1', component_property='children'),
     Output(component_id='div_outputVoc1', component_property='className')],
    [Input(component_id='inputVoc1', component_property='value'),
     Input(component_id='inputVoc1', component_property='n_submit')]
)
def update_answer(txt_inserted, n_submit):
    if n_submit is None:
        raise PreventUpdate
    else:
        return right_answer(txt_inserted, 9)

@app.callback(
    [Output(component_id='div_outputVoc2', component_property='children'),
     Output(component_id='div_outputVoc2', component_property='className')],
    [Input(component_id='inputVoc2', component_property='value'),
     Input(component_id='inputVoc2', component_property='n_submit')]
)
def update_answer(txt_inserted, n_submit):
    if n_submit is None:
        raise PreventUpdate
    else:
        return right_answer(txt_inserted, 10)

@app.callback(
    [Output(component_id='dropdown_output3', component_property='children'),
     Output(component_id='dropdown_output3', component_property='className')],
    Input('demo-dropdown3', 'value')
)
def update_output(value):
    if value is None:
        raise PreventUpdate
    else:
        return right_answer(value, 11)

@app.callback(
    [Output(component_id='div_outputVoc3', component_property='children'),
     Output(component_id='div_outputVoc3', component_property='className')],
    [Input(component_id='inputVoc3', component_property='value'),
     Input(component_id='inputVoc3', component_property='n_submit')]
)
def update_answer(txt_inserted, n_submit):
    if n_submit is None:
        raise PreventUpdate
    else:
        return right_answer(txt_inserted, 12)

@app.callback(
    Output('page-content', 'children'),
    Input('url', 'pathname')
)
def display_page(pathname):
    if pathname == '/learnIdioms':
        return learnIdioms_layout
    elif pathname == '/learnPhV':
        return learnPhV_layout
    elif pathname == '/learnVoc':
        return learnVoc_layout
    elif pathname == '/testIdioms':
        return testIdioms_layout
    elif pathname == '/testPhV':
        return testPhV_layout
    elif pathname == '/testVoc':
        return testVoc_layout
    elif pathname == '/translator':
        return translator_layout
    else:
        return index_page

if __name__ == '__main__':
   app.run_server(debug=True)
