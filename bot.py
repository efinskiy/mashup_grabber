import os
import requests.exceptions
import telebot
from ext import bot, mashup, db, COOKIES, LOG_CHAT_ID
import traceback
import time
from models import User, Channels
from sqlalchemy import and_
from datetime import datetime
import requests

SAVE_DIR = os.getcwd()


@bot.message_handler(commands=['start'])
def new_command(message: telebot.types.Message):
    session = db.Session()
    print(f'{datetime.now().strftime("%H:%M:%S %d.%m.%Y")} - New message from {message.from_user.id}')

    if session.scalars(
            User.select().where(
                User.uid == message.from_user.id
            )
    ).first():
        bot.send_message(reply_to_message_id=message.id, chat_id=message.chat.id, text='Already registered')
    else:
        session.add(User(uid=message.from_user.id, is_admin=True))
        session.commit()
        bot.send_message(reply_to_message_id=message.id, chat_id=message.chat.id, text='Now, you are registered')


@bot.channel_post_handler(content_types=['photo', 'audio', 'text'])
def new_post(message: telebot.types.Message):
    print(f'New message with type: {message.content_type}, chat: {message.chat.title}({message.chat.id})')
    session = db.Session()
    if not session.scalars(
            Channels.select().where(
                    Channels.chat_id == message.chat.id
                )
            ).first():
        session.add(Channels(chat_id=message.chat.id, enabled=False, title=message.chat.title))
        session.commit()

    is_custom_upload = session.scalars(
        Channels.select().where(
            Channels.chat_id == message.chat.id
        )
    ).first().upload_to_custom

    if is_custom_upload:
        log_chat_id = -1001844555588
    else:
        log_chat_id = LOG_CHAT_ID

    if message.content_type == 'audio' and message.reply_to_message is not None \
            and message.reply_to_message.content_type == 'photo':

        if not session.scalars(
                Channels.select().where(
                    and_(
                        Channels.chat_id == message.chat.id,
                        Channels.enabled == True
                    )
                )).first():
            bot.send_message(chat_id=log_chat_id,
                             text=f'<b>Контент от не одобренного источника</b>: <i>{message.chat.title}({message.chat.id})</i>')
            return None
        processing_msg_id = bot.send_message(log_chat_id, f'{message.audio.file_name} Обработка...').id
        try:
            albumCover = message.reply_to_message.photo[3]
            audio = message.audio

            audioDownload = requests.get(bot.get_file_url(audio.file_id)).content
            albumCoverDownload = requests.get(bot.get_file_url(albumCover.file_id)).content

        except Exception as e:
            bot.edit_message_text(chat_id=log_chat_id, message_id=processing_msg_id,
                             text=f'''❌ Произошла ошибка при получении контента
                             <code>
                             {str(traceback.format_exc())}
                             </code>''',
                             parse_mode='html'
                             )
            return

        try:
            with open(SAVE_DIR + "/temp_files/" + 'album_cover.jpg', 'wb') as new_file:
                new_file.write(albumCoverDownload)
                new_file.close()

            with open(SAVE_DIR + "/temp_files/" + audio.file_name, 'wb') as new_file:
                new_file.write(audioDownload)
                new_file.close()

            bot.send_message(message.chat.id, f'{audio.title} - {audio.performer}, {audio.file_name}')
            mashup.addAlbumCover(SAVE_DIR + "/temp_files/" + audio.file_name,
                                 SAVE_DIR + "/temp_files/" + 'album_cover.jpg')
            mashup.setTrackInfo(SAVE_DIR + "/temp_files/" + audio.file_name)
        except Exception as e:
            bot.edit_message_text(chat_id=log_chat_id, message_id=processing_msg_id,
                             text=f'''❌ Произошла ошибка при сохранении контента
                             <code>
                             {str(traceback.format_exc())}
                             </code>''',
                             parse_mode='html'
                             )
            return

        try:
            if is_custom_upload:
                _kind = 1016
            else:
                _kind = 1014
            postTarget = mashup.ugcUpload(filename=audio.file_name,
                                          kind=_kind,
                                          lang='ru',
                                          overembed=False,
                                          ncrnd=None,
                                          external_domain=None,
                                          visibility='public',
                                          bot=bot
                                          )
            if not postTarget:
                bot.edit_message_text(chat_id=log_chat_id, message_id=processing_msg_id,
                                      text=f'''❌ <b>Произошла ошибка при получении ссылки ugcUpload</b>
                                 <b>Chat</b>: {message.chat.title}({message.chat.id}),
                                 <b>Message id</b>: {message.id}
                                 ''',
                                 parse_mode='html'
                                 )
                return

            mashup.uploadTrack(file=open(SAVE_DIR + "/temp_files/" + audio.file_name, 'rb'),
                               post_target=postTarget,
                               cookies=COOKIES, kind=_kind)
        except Exception as e:
            bot.edit_message_text(chat_id=log_chat_id, message_id=processing_msg_id,
                                  text=f'''❌ <b>Произошла ошибка при загрузке контента в Яндекс.Музыку</b>
                             <b>Chat</b>: {message.chat.title}({message.chat.id}),
                             <b>Message id</b>: {message.id}
                             <code>
                             {str(traceback.format_exc())}
                             </code>
                             ''',
                             parse_mode='html'
                             )
            return
        bot.edit_message_text(chat_id=log_chat_id, message_id=processing_msg_id,
                              text=f'✅ Загружен трек: <i>{audio.file_name}</i>', parse_mode='html')


def start_polling():
    try:
        print(f'{datetime.now().strftime("%H:%M:%S %d.%m.%Y")} - Bot name: {bot.get_me().full_name}')
        bot.polling(non_stop=True, interval=0)

    except requests.exceptions.ReadTimeout:
        print(f'{datetime.now().strftime("%H:%M:%S %d.%m.%Y")} - Connection lost, retrying after 5 seconds')
        time.sleep(5)
        start_polling()
    except Exception as e:
        print(f'{datetime.now().strftime("%H:%M:%S %d.%m.%Y")} - Unknown exception, retrying after 5 seconds')
        print(traceback.format_exc())
        time.sleep(5)
        start_polling()


if __name__ == "__main__":
    print(f'{datetime.now().strftime("%H:%M:%S %d.%m.%Y")} - Start polling')
    print(f'{datetime.now().strftime("%H:%M:%S %d.%m.%Y")} - Log chat id: {LOG_CHAT_ID}')
    start_polling()


