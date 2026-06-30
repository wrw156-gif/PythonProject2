[app]
title = 출입마스터
package.name = qrmaster
package.domain = org.test
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf
version = 1.0
requirements = python3, kivy, android, jnius
android.permissions = RECEIVE_SMS, READ_SMS, RECEIVE_WAP_PUSH, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE, FOREGROUND_SERVICE, POST_NOTIFICATIONS
services = smsservice:service.py
android.api = 33
android.minapi = 21
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True

[buildozer]
log_level = 2
warn_on_root = 1