[app]
title = 출입마스터
package.name = qrmaster
package.domain = org.test
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf
version = 1.0
# 💡 [핵심 패치] 앱 내부에 들어갈 버전을 가장 안정적인 버전으로 강제 고정!
requirements = python3==3.11.9, kivy==2.3.0, android, pyjnius
android.permissions = RECEIVE_SMS, READ_SMS, RECEIVE_WAP_PUSH, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE, FOREGROUND_SERVICE, POST_NOTIFICATIONS
services = smsservice:service.py
android.api = 33
android.minapi = 21
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True

[buildozer]
log_level = 2
warn_on_root = 1
