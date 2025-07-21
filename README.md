Qiranas



Qiranas — это инструмент для изучения японского и арабского языков, который позволяет быстро получать перевод и чтение выделенного слова из любого приложения (игры, браузера, PDF и т.д.), а также добавлять найденные слова в Anki для последующего закрепления.

Программа поддерживает работу со словарями в формате zip-файлов, умеет распознавать текст с экрана (OCR), поддерживает горячие клавиши и поддерживает настройку через конфиг.

Возможности



&nbsp;   Получение перевода и чтения выделенного слова

&nbsp;   OCR для японского и арабского текста с экрана

&nbsp;   Работа со словарями

&nbsp;   Интеграция с Anki через AnkiConnect (создание карточек в выбранной колоде)

&nbsp;   Гибкая настройка горячих клавиш и колоды через config.txt

&nbsp;   Окно с результатами, возможностью скрывать отдельные переводы и открывать дочерние окна для новых слов

&nbsp;   Копирование текста из окна результатов



Установка



&nbsp;   Склонируйте репозиторий:



text



git clone https://github.com/bernkastel5/Qiranas.git

cd Qiranas



Установите зависимости:



text



&nbsp;   pip install -r requirements.txt



&nbsp;   Установите Anki и AnkiConnect:

&nbsp;       Скачать Anki

&nbsp;       В Anki: Инструменты → Дополнения → Получить дополнение → введите код 2055492159 (AnkiConnect).



&nbsp;   Скачайте и поместите словари:

&nbsp;       Поместите zip-словари в папку resources/dictionaries/.



Также, для работы должен быть установлен шаблон JP Mining Note в Anki (https://github.com/Aquafina-water-bottle/jp-mining-note)



Настройка



&nbsp;   config.txt

&nbsp;   В файле config.txt можно настроить горячие клавиши и название колоды для майнинга.

&nbsp;   Пример содержимого:



text



&nbsp;   on\_hotkey\_clipboard = alt+ctrl+q

&nbsp;   on\_hotkey\_ocr\_ja = ctrl+shift+y

&nbsp;   on\_hotkey\_ocr\_ar = ctrl+shift+a

&nbsp;   deckName = Mining



&nbsp;   Словари

&nbsp;   Просто добавьте новые zip-файлы в папку resources/dictionaries/ — программа подхватит их автоматически.



Запуск



text



python main.py



Использование



&nbsp;   Получить перевод выделенного слова:

&nbsp;       Выделите слово в тексте.

&nbsp;	Нажмите Ctrl+C.

&nbsp;       Нажмите горячую клавишу (по умолчанию Alt+Ctrl+Q).

&nbsp;       Откроется окно с переводом и чтением из всех подключённых словарей.



&nbsp;   Распознать текст с экрана (OCR):

&nbsp;       Нажмите горячую клавишу для японского (по умолчанию Ctrl+Shift+Y) или арабского (по умолчанию Ctrl+Shift+A).

&nbsp;       Выделите область экрана с нужным словом.

&nbsp;       Откроется окно с результатом распознавания и переводом.



&nbsp;   Работа с окном результатов:

&nbsp;       Кнопка "+" — добавить выбранные переводы в Anki.

&nbsp;       Кнопка "-" напротив перевода — скрыть этот перевод (он не попадёт в карточку).

&nbsp;       Двойной клик по слову или выделенному тексту — открыть новое окно с результатами для этого слова.

&nbsp;       Можно выделять и копировать текст из окна.



&nbsp;   Интеграция с Anki:

&nbsp;       Карточки добавляются в колоду, указанную в config.txt (deckName), по умолчанию стоит колода Mining.

&nbsp;       Для работы Anki должен быть запущен, а AnkiConnect — установлен.



Советы и ответы на возможные вопросы



&nbsp;   Если OCR не распознаёт текст, увеличьте разрешение или приблизьте текст. Для арабского текста - выделяйте основу слова, без артикля и без аффиксов, выражающих отношение (например в слове كتبناها выделять كتبنا).

&nbsp;     Если хотите добавить новые языки — добавьте соответствующие словари. Выделять можно текст на любом языке, OCR пока поддерживает арабский, японский и английский (по той же горячей клавише, что и японский). Для остальных языков работоспособность пока не гарантирована.

&nbsp;   Если хотите изменить горячие клавиши или колоду — просто отредактируйте config.txt.

&nbsp;   Если при активации горячей клавиши браузер или другое приложение ведёт себя странно (переключается окно, изменяется громкость и т.д.) - измените горячую клавишу.

&nbsp;   Если в окне с выдержками из словарей не написан перевод, а обозначено только какая форма какого слова замечена - прокрутите вниз. Если всё ещё не появилось фрейма с переводом - выделите слово, которое предлагает словарь как основу и посмотрите его через дочернее окно

&nbsp;   Если выделили слово, но двойной клик по нему не открывает дочернее окно - попробуйте быстро кликать несколько раз подряд рядом с этим словом в той строке окна словаря, в которой находится слово

&nbsp;   Если слова не распознаются, проверьте через консоль запущена ли программа. Если оно по какой-то причине остановилось - запустите снова. Если консоль выдала ошибку и после этого слова не распознаются - закройте и перезапустите приложение. Если консоль не выдаёт предупреждений, но слова всё равно не выделяются - попробуйте использовать внешнюю клавиатуру и/или перезапустите приложение. Если и это не помогает - перезапустите устройство

&nbsp;   Если карточка в Anki не создаётся, проверьте, установлен ли шаблон JP Mining Note в Anki для той колоды, в которую вы пытаетесь добавить карточку







Qiranas is a tool for learning Japanese and Arabic that allows you to quickly get the translation and reading of a selected word from any application (game, browser, PDF, etc.), as well as add found words to Anki for further reinforcement. The program supports working with dictionaries in zip file format, can recognize text from the screen (OCR), supports hotkeys, and can be configured via a config file.



Features



&nbsp;   Getting the translation and reading of a selected word

&nbsp;   OCR for Japanese and Arabic text from the screen

&nbsp;   Working with dictionaries

&nbsp;   Integration with Anki via AnkiConnect (creating cards in the selected deck)

&nbsp;   Flexible configuration of hotkeys and deck via config.txt

&nbsp;   Results window with the ability to hide individual translations and open child windows for new words

&nbsp;   Copying text from the results window



Installation



&nbsp;   Clone the repository:



text



git clone https://github.com/bernkastel5/Qiranas.git cd Qiranas



&nbsp;   Install dependencies:



text



pip install -r requirements.txt



&nbsp;   Install Anki and AnkiConnect:

&nbsp;       Download Anki

&nbsp;       In Anki: Tools → Add-ons → Get Add-ons → enter code 2055492159 (AnkiConnect).



&nbsp;   Download and place dictionaries:

&nbsp;       Place zip dictionaries in the resources/dictionaries/ folder.



Also, for the program to work, the JP Mining Note template must be installed in Anki (https://github.com/Aquafina-water-bottle/jp-mining-note)



Configuration



&nbsp;   config.txt In the config.txt file, you can configure hotkeys and the name of the mining deck. Example content:



text



on\_hotkey\_clipboard = alt+ctrl+q on\_hotkey\_ocr\_ja = ctrl+shift+y on\_hotkey\_ocr\_ar = ctrl+shift+a deckName = Mining



&nbsp;   Dictionaries Just add new zip files to the resources/dictionaries/ folder — the program will pick them up automatically.



Running



text



python main.py



Usage



&nbsp;   Get the translation of a selected word:

&nbsp;       Select a word in the text.

&nbsp;       Press Ctrl+C.

&nbsp;       Press the hotkey (by default Alt+Ctrl+Q).

&nbsp;       A window will open with the translation and reading from all connected dictionaries.



&nbsp;   Recognize text from the screen (OCR):

&nbsp;       Press the hotkey for Japanese (by default Ctrl+Shift+Y) or Arabic (by default Ctrl+Shift+A).

&nbsp;       Select the area of the screen with the desired word.

&nbsp;       A window will open with the recognition result and translation.



&nbsp;   Working with the results window:

&nbsp;       The "+" button — add the selected translations to Anki.

&nbsp;       The "-" button next to a translation — hide this translation (it will not be added to the card).

&nbsp;       Double-click on a word or selected text — open a new window with results for this word.

&nbsp;       You can select and copy text from the window.



&nbsp;   Integration with Anki:

&nbsp;       Cards are added to the deck specified in config.txt (deckName), by default the Mining deck.

&nbsp;       Anki must be running and AnkiConnect must be installed.



Tips and answers to possible questions



&nbsp;   If OCR does not recognize text, increase the resolution or zoom in on the text. For Arabic text — select the root of the word, without the article and without affixes expressing relation (for example, in the word كتبناها select كتبنا).

&nbsp;   If you want to add new languages — add the corresponding dictionaries. You can select text in any language, OCR currently supports Arabic, Japanese, and English (with the same hotkey as Japanese). For other languages, functionality is not guaranteed yet.

&nbsp;   If you want to change hotkeys or the deck — just edit config.txt.

&nbsp;   If, when activating a hotkey, the browser or another application behaves strangely (window switches, volume changes, etc.) — change the hotkey.

&nbsp;   If the results window does not show a translation, but only indicates which form of which word is detected — scroll down. If there is still no frame with a translation — select the word that the dictionary suggests as the base and look it up through a child window.

&nbsp;   If you selected a word but double-clicking on it does not open a child window — try quickly clicking several times next to this word in the line of the dictionary window where the word is located.

&nbsp;   If words are not recognized, check in the console whether the program is running. If it has stopped for some reason — restart it. If the console gave an error and after that words are not recognized — close and restart the application. If the console does not give warnings, but words still are not selected — try using an external keyboard and/or restart the application. If that does not help — restart the device.

&nbsp;   If a card is not created in Anki, check whether the JP Mining Note template is installed in Anki for the deck you are trying to add the card to.



&nbsp;   



