[app]
title = Flashcards Italiano
package.name = flashcards_italiano
package.domain = com.flashcards.italiano

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json

version = 1.0
requirements = python3,kivy,pandas,openpyxl,gtts,pygame

[android]
api = 33
minapi = 21
ndk = 25b
private_storage = True
permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
orientation = portrait
android.theme = @android:style/Theme.NoTitleBar

[buildozer]
log_level = 2