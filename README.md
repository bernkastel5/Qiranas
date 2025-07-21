Qiranas

Qiranas — это инструмент для изучения японского и арабского языков, который позволяет быстро получать перевод и чтение выделенного слова из любого приложения (игры, браузера, PDF и т.д.), а также добавлять найденные слова в Anki для последующего закрепления.

Программа поддерживает работу со словарями в формате .zip-файлов, умеет распознавать текст с экрана (OCR), поддерживает горячие клавиши и настройку через конфиг.
Возможности

    Получение перевода и чтения выделенного слова
    OCR для японского и арабского текста с экрана
    Работа со словарями
    Интеграция с Anki через AnkiConnect (создание карточек в выбранной колоде)
    Гибкая настройка горячих клавиш и колоды через config.txt
    Окно с результатами, возможностью скрывать отдельные переводы и открывать дочерние окна для новых слов
    Копирование текста из окна результатов

Установка

    Склонируйте репозиторий:

Bash

git clone https://github.com/bernkastel5/Qiranas.git
cd Qiranas

Установите зависимости:

Bash

    pip install -r requirements.txt

    Установите Anki и AnkiConnect:
        Скачать Anki
        В Anki: Инструменты → Дополнения → Получить дополнение → введите код 2055492159 (AnkiConnect).

    Скачайте и поместите словари:
        Поместите .zip-словари в папку resources/dictionaries/.

    Важно: Для работы должен быть установлен шаблон JP Mining Note в Anki.

Настройка
config.txt

В файле config.txt можно настроить горячие клавиши и название колоды для майнинга.

Пример содержимого:

ini

on_hotkey_clipboard = alt+ctrl+q
on_hotkey_ocr_ja = ctrl+shift+y
on_hotkey_ocr_ar = ctrl+shift+a
deckName = Mining

Словари

Просто добавьте новые .zip-файлы в папку resources/dictionaries/ — программа подхватит их автоматически.
Запуск

Bash

python main.py

Использование

Получить перевод выделенного слова:

    Выделите слово в тексте.
    Нажмите Ctrl+C.
    Нажмите горячую клавишу (по умолчанию Alt+Ctrl+Q).
    Откроется окно с переводом и чтением из всех подключённых словарей.

Распознать текст с экрана (OCR):

    Нажмите горячую клавишу для японского (по умолчанию Ctrl+Shift+Y) или арабского (по умолчанию Ctrl+Shift+A).
    Выделите область экрана с нужным словом.
    Откроется окно с результатом распознавания и переводом.

Работа с окном результатов:

    Кнопка + — добавить выбранные переводы в Anki.
    Кнопка - напротив перевода — скрыть этот перевод (он не попадёт в карточку).
    Двойной клик по слову или выделенному тексту — открыть новое окно с результатами для этого слова.
    Можно выделять и копировать текст из окна.

Интеграция с Anki:

    Карточки добавляются в колоду, указанную в config.txt (deckName), по умолчанию стоит колода Mining.
    Для работы Anki должен быть запущен, а AnkiConnect — установлен.

Советы и ответы на возможные вопросы

    Если OCR не распознаёт текст, увеличьте разрешение или приблизьте текст. Для арабского текста - выделяйте основу слова, без артикля и без аффиксов, выражающих отношение (например в слове كتبناها выделять كتبنا).
    Если хотите добавить новые языки — добавьте соответствующие словари. Выделять можно текст на любом языке, OCR пока поддерживает арабский, японский и английский (по той же горячей клавише, что и японский). Для остальных языков работоспособность пока не гарантирована.
    Если хотите изменить горячие клавиши или колоду — просто отредактируйте config.txt.
    Если при активации горячей клавиши браузер или другое приложение ведёт себя странно (переключается окно, изменяется громкость и т.д.) - измените горячую клавишу.
    Если в окне с выдержками из словарей не написан перевод, а обозначено только какая форма какого слова замечена - прокрутите вниз. Если всё ещё не появилось фрейма с переводом - выделите слово, которое словарь предлагает как основу, и посмотрите его через дочернее окно.
    Если выделили слово, но двойной клик по нему не открывает дочернее окно - попробуйте быстро кликать несколько раз подряд рядом с этим словом в той строке окна словаря, в которой находится слово.
    Если слова не распознаются, проверьте через консоль, запущена ли программа. Если она по какой-то причине остановилась - запустите снова. Если консоль выдала ошибку и после этого слова не распознаются - закройте и перезапустите приложение. Если консоль не выдаёт предупреждений, но слова всё равно не выделяются - попробуйте использовать внешнюю клавиатуру и/или перезапустите приложение. Если и это не помогает - перезапустите устройство.
    Если карточка в Anki не создаётся, проверьте, установлен ли шаблон JP Mining Note в Anki для той колоды, в которую вы пытаетесь добавить карточку.

<br>
Qiranas

Qiranas is a tool for learning Japanese and Arabic that allows you to quickly get the translation and reading of a selected word from any application (game, browser, PDF, etc.), as well as add found words to Anki for further reinforcement. The program supports working with dictionaries in .zip file format, can recognize text from the screen (OCR), supports hotkeys, and can be configured via a config file.
Features

    Getting the translation and reading of a selected word
    OCR for Japanese and Arabic text from the screen
    Working with dictionaries
    Integration with Anki via AnkiConnect (creating cards in the selected deck)
    Flexible configuration of hotkeys and deck via config.txt
    Results window with the ability to hide individual translations and open child windows for new words
    Copying text from the results window

Installation

    Clone the repository:

Bash

git clone https://github.com/bernkastel5/Qiranas.git 
cd Qiranas

Install dependencies:

Bash

    pip install -r requirements.txt

    Install Anki and AnkiConnect:
        Download Anki
        In Anki: Tools → Add-ons → Get Add-ons → enter code 2055492159 (AnkiConnect).

    Download and place dictionaries:
        Place .zip dictionaries in the resources/dictionaries/ folder.

    Note: For the program to work, the JP Mining Note template must be installed in Anki.

Configuration
config.txt

In the config.txt file, you can configure hotkeys and the name of the mining deck.

Example content:

ini

on_hotkey_clipboard = alt+ctrl+q 
on_hotkey_ocr_ja = ctrl+shift+y 
on_hotkey_ocr_ar = ctrl+shift+a 
deckName = Mining

Dictionaries

Just add new .zip files to the resources/dictionaries/ folder — the program will pick them up automatically.
Running

Bash

python main.py

Usage

Get the translation of a selected word:

    Select a word in the text.
    Press Ctrl+C.
    Press the hotkey (by default Alt+Ctrl+Q).
    A window will open with the translation and reading from all connected dictionaries.

Recognize text from the screen (OCR):

    Press the hotkey for Japanese (by default Ctrl+Shift+Y) or Arabic (by default Ctrl+Shift+A).
    Select the area of the screen with the desired word.
    A window will open with the recognition result and translation.

Working with the results window:

    The + button — add the selected translations to Anki.
    The - button next to a translation — hide this translation (it will not be added to the card).
    Double-click on a word or selected text — open a new window with results for this word.
    You can select and copy text from the window.

Integration with Anki:

    Cards are added to the deck specified in config.txt (deckName), by default the Mining deck.
    Anki must be running and AnkiConnect must be installed.

Tips and answers to possible questions

    If OCR does not recognize text, increase the resolution or zoom in on the text. For Arabic text — select the root of the word, without the article and without affixes expressing relation (for example, in the word كتبناها select كتبنا).
    If you want to add new languages — add the corresponding dictionaries. You can select text in any language; OCR currently supports Arabic, Japanese, and English (with the same hotkey as Japanese). For other languages, functionality is not guaranteed yet.
    If you want to change hotkeys or the deck — just edit config.txt.
    If, when activating a hotkey, the browser or another application behaves strangely (window switches, volume changes, etc.) — change the hotkey.
    If the results window does not show a translation, but only indicates which form of which word is detected — scroll down. If there is still no frame with a translation — select the word that the dictionary suggests as the base and look it up through a child window.
    If you selected a word but double-clicking on it does not open a child window — try quickly clicking several times next to this word in the line of the dictionary window where the word is located.
    If words are not recognized, check in the console whether the program is running. If it has stopped for some reason — restart it. If the console gave an error and after that words are not recognized — close and restart the application. If the console does not give warnings, but words still are not selected — try using an external keyboard and/or restart the application. If that does not help — restart the device.
    If a card is not created in Anki, check whether the JP Mining Note template is installed in Anki for the deck you are trying to add the card to.
