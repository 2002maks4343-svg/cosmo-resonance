[app]
title = Космо-Резонанс
package.name = cosmo_resonance
package.domain = com.maxim.cosmo

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,wav,mp3,ttf

version = 1.0

requirements = python3,kivy,pillow,numpy

orientation = portrait
fullscreen = 0

# Иконка (если нет — закомментируй)
# icon.filename = %(source.dir)s/assets/icon.png

android.permissions = INTERNET, WRITE_EXTERNAL_STORAGE

android.api = 33
android.minapi = 24
android.ndk = 25b
android.archs = arm64-v8a, armeabi-v7a

# Настройки экрана
android.wakelock = 1

# Kivy
osx.kivy_version = 2.3.1

# Автопринятие лицензий SDK
android.accept_sdk_license = True
android.skip_update = False
