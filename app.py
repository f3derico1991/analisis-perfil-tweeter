import matplotlib
matplotlib.use('Agg')

from flask import Flask, render_template, request
import tweepy
from datetime import datetime
import pytz
import pandas as pd
import requests
import matplotlib.pyplot as plt
import seaborn as sns
import os
import io
from PIL import Image
import threading
import locale

app = Flask(__name__)

def plot_graph1(df):
    hour_count = df['Fecha'].dt.hour.value_counts().sort_index()
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.lineplot(x=hour_count.index, y=hour_count.values, ax=ax)
    ax.set_xticks(range(24))
    ax.set_xticklabels([f'{i} hs' for i in range(24)], rotation=45)
    ax.set_xlabel('Hora')
    ax.set_ylabel('Cantidad de Tweets')
    graph1_path = 'static/graph1.png'
    fig.savefig(graph1_path)

def plot_graph2(df):
    locale.setlocale(locale.LC_TIME, 'es_ES')
    # Obtener los nombres de los días de la semana en español y en el orden correcto
    df['Dia de la semana'] = df['Fecha'].dt.strftime('%A').str.capitalize()
    dias_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    counts = df['Dia de la semana'].value_counts().reindex(dias_semana, fill_value=0)
    fig2 = sns.lineplot(x=counts.index, y=counts.values)
    fig2.set_xlabel('Día de la semana')
    fig2.set_ylabel('Cantidad de tweets')
    fig2.set(title='Cantidad de tweets según día de la semana')
    fig2.set_xticks(range(len(counts.index)))
    fig2.set_xticklabels(counts.index)
    graph2_path = 'static/graph2.png'
    fig2.figure.savefig(graph2_path)

@app.route('/')
def formulario():
    return render_template('formulario.html')

@app.route('/procesar_formulario', methods=['POST'])
def procesar_formulario():
    nombreusuario = request.form['username']
    
    # Aquí se deben ingresar las credenciales de la API de Twitter
    consumer_key = 'h2Wm2Kq5WqNfpHyPycMIRFUYm'
    consumer_secret = 'lhM1VzJBf5472dn6lkWxyI0UfRikGSNCDlbuxYObrVr5ysDLv9'
    access_token = '1328065364-y7UX9joKeQcXFMV2kDH76hJJMdWoWETnWbBE5NT'
    access_token_secret = 'AsKyEEoC3fbNoLMOev6nWDmK8sv6qrfk92N9JOBio6EcF'

    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth)

    try:
        user = api.get_user(screen_name=nombreusuario)
    except tweepy.error.TweepError as e:
        if e.response.status_code == 404:
            return render_template('error.html', error_message='El usuario no existe en Twitter.')
        else:
            return render_template('error.html', error_message='Ocurrió un error al obtener los datos del usuario.')

    tweets = tweepy.Cursor(api.user_timeline, id=nombreusuario, tweet_mode='extended').items()

    tweet_data = []
    for tweet in tweets:
        fecha = tweet.created_at.astimezone(pytz.timezone('America/Argentina/Buenos_Aires')).replace(tzinfo=None)
        likes = tweet.favorite_count
        retweets = tweet.retweet_count
        id_tweet = tweet.id
        lang = tweet.lang
        is_retweet = tweet.retweeted

        tweet_data.append({
            'Tweet_id': id_tweet,
            'Fecha': fecha,
            'Likes': likes,
            'Retweets': retweets,
            'Idioma': lang,
            'Es_Retweet': is_retweet
        })

    df = pd.DataFrame(tweet_data)

    profile_image_url = user.profile_image_url_https
    response = requests.get(profile_image_url)
    with open('static/profile_image.jpg', 'wb') as f:
        f.write(response.content)

    tweet_max_likes = df.iloc[df['Likes'].idxmax()]
    tweet_mxlk = api.get_status(tweet_max_likes['Tweet_id'], tweet_mode='extended')
    top_likes = (f'Tweet con más likes: {tweet_mxlk.full_text}\n'
                 f'Fecha: {tweet_max_likes["Fecha"]}\n'
                 f'Cantidad de likes: {tweet_max_likes["Likes"]}\n'
                 f'Cantidad de retweets: {tweet_max_likes["Retweets"]}\n'
                 f'Tweet_id: {tweet_max_likes["Tweet_id"]}\n')

    tweet_max_rt = df.iloc[df['Retweets'].idxmax()]
    tweet_mxrt = api.get_status(tweet_max_rt['Tweet_id'], tweet_mode='extended')
    top_rt = (f'Tweet con más retweets: {tweet_mxrt.full_text}\n'
               f'Fecha: {tweet_max_rt["Fecha"]}\n'
               f'Cantidad de likes: {tweet_max_rt["Likes"]}\n'
               f'Cantidad de retweets: {tweet_max_rt["Retweets"]}\n'
               f'Tweet_id: {tweet_max_rt["Tweet_id"]}\n')

    # Llama a las funciones plot_graph1 y plot_graph2 dentro de hilos separados para generar los gráficos
    t1 = threading.Thread(target=plot_graph1, args=(df,))
    t2 = threading.Thread(target=plot_graph2, args=(df,))
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    return render_template('templates.html',
                           username=nombreusuario,
                           user_image='static/profile_image.jpg',
                           top_likes=top_likes,
                           top_rt=top_rt,
                           graph1_image='static/graph1.png',
                           graph2_image='static/graph2.png')

if __name__ == '__main__':
    app.run()


