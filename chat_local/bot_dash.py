#import glob

import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
from rasa_core.agent import Agent
#from rasa_nlu.model import Interpreter
from rasa_core.interpreter import RasaNLUInterpreter
#from rasa_nlu.config import RasaNLUConfig

#import utils.bot
#from utils.downloader import download_charts
from rasa_core.actions import Action
from rasa_core.actions.forms import FormAction
from datetime import datetime ,timedelta
"""
# read in most recent model build
model_dirs = sorted(glob.glob('./rasa_model/default/model_*/'))
model_path = model_dirs[-1]

# define config
args = {'pipeline': 'spacy_sklearn'}
config = RasaNLUConfig(cmdline_args=args)

# where `model_directory points to the folder the model is persisted in
interpreter = Interpreter.load(model_path, config)

# update chart data.. use back up data if error
try:
    app_data_path = 'data/app_chart_data.csv'
    download_charts(app_data_path)
except:
    print('using backup app data')
    app_data_path = 'data/backup_app_chart_data.csv'
# --------------------------------------------------
"""


# init app and add stylesheet
app = dash.Dash()
app.css.append_css({"external_url": "https://codepen.io/chriddyp/pen/bWLwgP.css"})

# init a list of the sessions conversation history
conv_hist = []

# app ui
app.layout = html.Div([
    html.H3('智能理财助手Demo V0.1', style={'text-align': 'center'}),
    # html.H3('Removed the real text'),
    # html.Img(src="https://thumbnail0.baidupcs.com/thumbnail/096cf1a5ad6a41f39a41c6ae97cf3cd7?fid=3226213234-250528-223386035414277&time=1532073600&rt=sh&sign=FDTAER-DCb740ccc5511e5e8fedcff06b081203-Wfc0%2B%2FgW4G%2FIZLxND%2FoEGyE2MF8%3D&expires=8h&chkv=0&chkbd=0&chkpc=&dp-logid=4654344113923524678&dp-callid=0&size=c710_u400&quality=100&vuk=-&ft=video", style={'align': 'right'}),
    html.Div([
        html.Div([
            html.Table([
                html.Tr([
                    # text input for user message
                    html.Td([dcc.Input(id='msg_input', value='你好', type='text')],
                            style={'valign': 'middle'}),                                              
                    # message to send user message to bot backend
                    html.Td([html.Button('Send', id='send_button', type='submit')],
                            style={'valign': 'middle'})                    
                ])
            ])],
            style={'width': '325px', 'margin': '0 auto'}),
        html.Br(),
        html.Div(id='conversation')],
        id='screen',
        style={'width': '400px', 'margin': '0 auto'})
])


# trigger bot response to user inputted message on submit button click
@app.callback(
    Output(component_id='conversation', component_property='children'),
    [Input(component_id='send_button', component_property='n_clicks')],
    #Input(component_id='btn_input', component_property='n_clicks')],
    state=[State(component_id='msg_input', component_property='value')]
    #State(component_id='btn_input', component_property='value')]
)


# function to add new user*bot interaction to conversation history
def update_conversation(click,text):
    global conv_hist
    global remind_time

    #print("*** "+str(click))
    # dont update on app load
    if click>0:
        
        # call bot with user inputted text
        # response, generic_response = utils.bot.respond(
        #     text,
        #     interpreter,
        #     app_data_path
        # )
        # now = datetime.now()
        text=text.strip()
        response = agent.handle_message(text)
        print(response)
        # if str(response).find('已经开启30s预定提醒')>=0:
        #     remind_time = now + timedelta(seconds=30)

        # user message aligned left
        rcvd = [html.H5(text, style={'text-align': 'right'})]
        # bot response aligned right and italics
        # rspd = [html.H5(html.I(r), style={'text-align': 'right'}) for r in response[0]['text']]
        res = ''
        # for r in response[-1:]:
        for r in response[:]:
            try:
                res += r['text']+'\n'
                i=1
                for d in r['data']:
                    res += '['+str(i)+'] '+ d['payload']+'\n'
                    i+=1
                #rspd += [html.H5(html.I(r['data']), style={'text-align': 'right'}) for r in response]
            except:
                pass

        rspd=[]
        for r in res.split('\n'):
            r = r.strip()
            if r[:4]=="http":
                rspd += ([html.Img(src=r)])
            elif r[0:1]=='[' and r[len(r)-1:len(r)]==']':
                rspd += ([html.H5(r, style={'text-align': 'left','color': '#600000'})])
            else:
                rspd += ([html.H5(r, style={'text-align': 'left','color': '#6495ED'})])
        # if generic_response:
        #     generic_msg = 'i couldn\'t find any specifics in your message, here are some popular apps:'
        #     rspd = [html.H6(html.I(generic_msg))] + rspd
        # append interaction to conversation history

        conv_hist =  rspd + rcvd + [html.Hr()] + conv_hist

        # check booking remind
        # if now>=remind_time:
        #     rcvd = [html.H5("您预定的产品就要开售了，请及时关注【陆金所VIP客服部】", style={'text-align': 'left','color': '#B22222'})]
        #     remind_time = now+ timedelta(days=1)
        #     conv_hist = rcvd + [html.Hr()] + conv_hist

        return conv_hist        
    else:
        return ''
  


@app.callback(
    Output(component_id='msg_input', component_property='value'),
    [Input(component_id='conversation', component_property='children')]
    #state=[State(component_id='btn_input', component_property='value')]
)
def clear_input(_):
    return ''


# run app
if __name__ == '__main__':
    
    interpreter = RasaNLUInterpreter('./models/vip/demo')
    agent = Agent.load('./models/dialogue', interpreter = interpreter)
    # remind_time = datetime.now()+ timedelta(days=1)   
    app.run_server()

