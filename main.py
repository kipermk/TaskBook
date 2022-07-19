import datetime
import sqlite3 as sl
import string

import PySimpleGUI as sg
import enchant
import pyperclip
from psgtray import SystemTray


def addToBase(task, dell=False):
    if task.strip():
        sqlite_connection = sl.connect('baseTask.db')
        with sqlite_connection:
            sqlite_connection.execute("""
                           CREATE TABLE IF NOT EXISTS TASK (
                               id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                               Task TEXT,
                               Date DateTime
                           );
                       """)
        try:
            cursor = sqlite_connection.cursor()

            info = cursor.execute("SELECT * FROM TASK where Task=?", (task,))
            row = info.fetchone()
            if row is None:
                cursor.execute("INSERT INTO TASK (Task, Date) VALUES (?,?);",
                               (task, datetime.datetime.now()))
                sqlite_connection.commit()
            else:
                if dell:
                    cursor.execute("DELETE FROM TASK where Task=?",
                                   (task,))
                else:
                    cursor.execute("Update TASK set Date = ? where Task=?",
                                   (datetime.datetime.now(), task))
                sqlite_connection.commit()
            cursor.close()

        except sl.Error as error:
            print("Ошибка при работе с SQLite", error)
        finally:
            if sqlite_connection:
                sqlite_connection.close()


def fromDase():
    try:
        con = sl.connect('baseTask.db')
        data = con.execute("SELECT Task FROM TASK ORDER BY Date DESC")
        return data.fetchall()
    except:
        return []


def startForm():
    dictionaryEn = enchant.Dict("en_US")
    dictionary = enchant.Dict("ru_RU")

    records = fromDase()
    layout = [
        [sg.Submit(button_text='Скопировать в буфер', key='-copy-'),
         sg.Submit(button_text='Х', size=(2), key='-clearchoiceTask-'),
         # sg.Text('                                                                             '),
         # sg.Text('                                                                              '),
         sg.Push(),
         sg.Submit(button_text='Скрыть', key='Hide')],
        [sg.Listbox(values=[], key='choiceTask', size=(60, 10), enable_events=True),
         sg.Listbox(values=[row[0] for row in records], key='fullTask', size=(60, 10), enable_events=True), ],

        [sg.Submit(button_text='Вставить из буфера', key='-past-'),
         sg.Submit(button_text='Х', size=(2), key='-clearmultiline-'),
         sg.Submit(button_text='Х', size=(2), key='-clearoutPut-'),
         sg.Push(),
         sg.Submit(button_text='Обновить', key='addtobase'),
         # sg.Text('                                                             '),
         sg.Submit(button_text='Удалить запись', key='-dellrecord-')],

        [sg.Multiline(size=(124, 5), disabled=False, key='multiline', enable_events=True)],
        [sg.Output(size=(124, 5), key='outPut')]

    ]
    # sg.theme('Light Green 6')
    window = sg.Window('Task book', layout, icon='Task.ico',
                       finalize=True)  # , finalize=True, enable_close_attempted_event=True)

    multiline = window['multiline']
    widget = multiline.Widget

    menu = ['', ['Вставить из буфера', 'Show', 'Hide', 'Exit']]
    tooltip = 'Task_book'

    tray = SystemTray(menu, single_click_events=False, window=window, tooltip=tooltip, icon='Task.ico')
    # tray.show_message('System Tray', 'System Tray Icon Started!')
    # sg.cprint(sg.get_versions())
    # col_vals = fromDase()
    # window.Element('fullTask').Update(values=col_vals)

    while True:  # The Event Loop
        event, values = window.read()

        if event == tray.key:
            event = values[event]

        if event == 'Вставить из буфера':
            window.un_hide()
            window.bring_to_front()
            multiline.Update('')
            event = '-past-'

        if event in (None, 'Exit', 'Cancel', sg.WIN_CLOSED):
            break

        elif event in ('Show', sg.EVENT_SYSTEM_TRAY_ICON_DOUBLE_CLICKED):
            window.un_hide()
            window.bring_to_front()

        elif event in ('Hide', sg.WIN_CLOSE_ATTEMPTED_EVENT):
            window.hide()
            tray.show_icon()

        elif event == '-clearoutPut-':
            window.Element('outPut').Update('')

        elif event == '-clearmultiline-':
            multiline.Update('')

        elif event == '-clearchoiceTask-':
            window.Element('choiceTask').Update('')

        elif event == '-dellrecord-':
            if len(values['fullTask']) != 0:
                output_var = values['fullTask'][0]
                addToBase(output_var, True)
            records = fromDase()
            window.Element('fullTask').Update(values=[row[0] for row in records])

        elif event == '-copy-':
            lst = window.Element('choiceTask').get_list_values()
            if len(lst) != 0:
                copyText = 'Задачи:' if len(lst) > 1 else 'Задача:'
                for i in lst:
                    copyText += '\n' + i

                print('Текст скопирован в буфер обмена')
                print(copyText)
                pyperclip.copy(copyText)

        elif event == '-past-':
            multiline.update(pyperclip.paste() + '\n', append=True)

        elif event == 'addtobase':
            for i in values["multiline"].split('\n'):
                addToBase(i)
            records = fromDase()
            window.Element('fullTask').Update(values=[row[0] for row in records])

        if event == 'fullTask':
            if len(values['fullTask']) != 0:
                output_var = values['fullTask'][0]
                lst = window.Element('choiceTask').get_list_values()
                lst.append(output_var)
                window.Element('choiceTask').Update(values=lst)
                addToBase(output_var)

        if event == 'choiceTask':
            if len(values['choiceTask']) != 0:
                output_var = values['choiceTask'][0]
                lst = window.Element('choiceTask').get_list_values()
                lst.remove(output_var)
                window.Element('choiceTask').Update(values=lst)

        if event == 'multiline':
            text = multiline.get()
            widget.tag_delete('WrogText')

            lines = text.split('\n')
            nline = 0
            for line in lines:
                nline += 1

                words_without_punctuation = line.translate(str.maketrans(dict.fromkeys(string.punctuation))).split()
                verifiable_words = []
                for w in words_without_punctuation:
                    if not dictionary.check(w) and not dictionaryEn.check(w):
                        verifiable_words.append(w)

                try:
                    widget.tag_config('WrogText', foreground='red')  # 'white')#, background='blue')
                    for w in verifiable_words:
                        ind = line.index(w)
                        widget.tag_add('WrogText', f'{nline}.{ind}', f'{nline}.{ind + len(w)}')
                except Exception as e:
                    pass
                    # print(e)

        if multiline.get():
            window.Element('addtobase').Update('Добавить')
        else:
            window.Element('addtobase').Update('Обновить')


if __name__ == "__main__":
    startForm()
