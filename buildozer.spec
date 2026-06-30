[app]
title = 출입마스터
package.name = qrmaster
package.domain = org.test
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf
version = 1.0
requirements = python3,kivy==2.3.0,android,pyjnius
android.permissions = RECEIVE_SMS, READ_SMS, RECEIVE_WAP_PUSH, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE, FOREGROUND_SERVICE, POST_NOTIFICATIONS
services = smsservice:service.py

# --- 버전 전부 고정 (불확실성 제거) ---
android.api = 33
android.minapi = 21
android.ndk = 25b
android.sdk = 33
android.accept_sdk_license = True
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True

# python-for-android 고정 (hostpython 3.11 → Cython 0.29.33 호환)
p4a.branch = v2024.01.21

[buildozer]
log_level = 2
warn_on_root = 1
