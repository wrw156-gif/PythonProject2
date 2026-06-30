import sqlite3, re, os, threading, queue
from datetime import datetime
from time import sleep
try:
    from jnius import autoclass, PythonJavaClass, java_method
    from android import PythonService
except: pass

message_queue = queue.Queue()

def init_db():
    conn = sqlite3.connect("master_attendance.db")
    conn.execute('''CREATE TABLE IF NOT EXISTS logs 
                    (id INTEGER PRIMARY KEY, date TEXT, mode TEXT, proj TEXT, name TEXT, 
                     phone TEXT, in_t TEXT, out_t TEXT, task_reason TEXT, health TEXT, photo TEXT)''')
    conn.commit(); conn.close()

def extract_mms_photo(ctx):
    photo_path = "사진없음"
    try:
        Uri = autoclass('android.net.Uri')
        uri = Uri.parse("content://mms/part")
        resolver = ctx.getContentResolver()
        cursor = resolver.query(uri, None, "ct LIKE 'image/%'", None, "mid DESC LIMIT 1")
        
        if cursor and cursor.moveToFirst():
            part_id = cursor.getString(cursor.getColumnIndex("_id"))
            part_uri = Uri.parse(f"content://mms/part/{part_id}")
            
            save_dir = "/storage/emulated/0/Download/QR_Photos/"
            if not os.path.exists(save_dir): os.makedirs(save_dir)
            
            filename = f"IMG_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.jpg"
            photo_path = os.path.join(save_dir, filename)
            
            is_stream = resolver.openInputStream(part_uri)
            os_stream = autoclass('java.io.FileOutputStream')(photo_path)
            buffer = autoclass('java.lang.reflect.Array').newInstance(autoclass('java.lang.Byte').TYPE, 4096)
            
            while True:
                read = is_stream.read(buffer)
                if read <= 0: break
                os_stream.write(buffer, 0, read)
                
            os_stream.close(); is_stream.close(); cursor.close()
    except Exception: pass
    return photo_path

def save_to_db(mode, type_, proj, name, phone, task_reason, time_val, health, photo_path):
    conn = sqlite3.connect("master_attendance.db", timeout=20.0)
    cur = conn.cursor()
    today_date = datetime.now().strftime("%Y-%m-%d")
    
    if mode == "상시": 
        if type_ == "퇴실":
            cur.execute("INSERT INTO logs (date, mode, proj, name, phone, in_t, out_t, task_reason, health, photo) VALUES (?,?,?,?,?,?,?,?,?,?)", 
                        (today_date, mode, proj, name, phone, "", time_val, task_reason, health, photo_path))
        else:
            cur.execute("INSERT INTO logs (date, mode, proj, name, phone, in_t, out_t, task_reason, health, photo) VALUES (?,?,?,?,?,?,?,?,?,?)", 
                        (today_date, mode, proj, name, phone, time_val, "", task_reason, health, photo_path))
    else: 
        cur.execute("SELECT id FROM logs WHERE date=? AND proj=? AND name=? ORDER BY id DESC LIMIT 1", (today_date, proj, name))
        open_rec = cur.fetchone()
        
        if type_ == "퇴실":
            if open_rec: cur.execute("UPDATE logs SET out_t=?, task_reason=?, health=?, photo=CASE WHEN ?!='사진없음' THEN ? ELSE photo END WHERE id=?", 
                                     (time_val, task_reason, health, photo_path, photo_path, open_rec[0]))
            else: cur.execute("INSERT INTO logs (date, mode, proj, name, phone, in_t, out_t, task_reason, health, photo) VALUES (?,?,?,?,?,?,?,?,?,?)", 
                              (today_date, mode, proj, name, phone, "", time_val, task_reason, health, photo_path))
        else:
            if open_rec: cur.execute("UPDATE logs SET in_t=?, task_reason=?, health=?, photo=CASE WHEN ?!='사진없음' THEN ? ELSE photo END WHERE id=?", 
                                     (time_val, task_reason, health, photo_path, photo_path, open_rec[0]))
            else: cur.execute("INSERT INTO logs (date, mode, proj, name, phone, in_t, out_t, task_reason, health, photo) VALUES (?,?,?,?,?,?,?,?,?,?)", 
                              (today_date, mode, proj, name, phone, time_val, "", task_reason, health, photo_path))
            
    conn.commit(); conn.close()

def queue_worker():
    while True:
        try:
            item = message_queue.get()
            body, sender, action, ctx = item['body'], item['sender'], item['action'], item['context']
            
            if action == "mms": sleep(3) 
                
            try:
                mode = "상시" if "SYS_QR_상시" in body else "작업"
                type_ = "퇴실" if "퇴실@#]" in body else "출입"
                
                proj_m = re.search(r'장소:\s*(.*?)\s*/', body)
                proj = proj_m.group(1).strip() if proj_m else "미지정"
                
                name_m = re.search(r'이름:\s*(.*?)\s*(?:\(|/)', body)
                name = name_m.group(1).strip() if name_m else "알수없음"
                
                task_m = re.search(r'내용:\s*(.*?)\s*\(시간', body)
                task_reason = task_m.group(1).strip() if task_m else "-"
                
                time_m = re.search(r'\(시간:\s*(.*?)\)', body)
                time_val = time_m.group(1).strip() if time_m else ""
                
                health_m = re.search(r'건강:\s*(.*)', body)
                health = health_m.group(1).strip() if health_m else "-"
                
                photo_file = extract_mms_photo(ctx)
                save_to_db(mode, type_, proj, name, sender, task_reason, time_val, health, photo_file)
            except Exception: pass
                
            message_queue.task_done()
        except Exception: pass

class MasterReceiver(PythonJavaClass):
    __javainterfaces__ = ['android/content/BroadcastReceiver']
    @java_method('(Landroid/content/Context;Landroid/content/Intent;)V')
    def onReceive(self, ctx, intent):
        action = intent.getAction()
        body, sender, msg_type = "", "010-0000-0000", "sms"
        
        if action == "android.provider.Telephony.SMS_RECEIVED":
            for pdu in intent.getExtras().get("pdus"):
                msg = autoclass('android.telephony.SmsMessage').createFromPdu(pdu)
                body += str(msg.getMessageBody())
                sender = str(msg.getOriginatingAddress())
        elif action == "android.provider.Telephony.WAP_PUSH_RECEIVED":
            msg_type = "mms"
            body = "SYS_QR_"
            
        if "SYS_QR_" in body:
            message_queue.put({'body': body, 'sender': sender, 'action': msg_type, 'context': ctx})

if __name__ == '__main__':
    init_db()
    threading.Thread(target=queue_worker, daemon=True).start()
    try:
        service_context = PythonService.mService
        f = autoclass('android.content.IntentFilter')("android.provider.Telephony.SMS_RECEIVED")
        f.addAction("android.provider.Telephony.WAP_PUSH_RECEIVED")
        f.addDataType("application/vnd.wap.mms-message")
        service_context.registerReceiver(MasterReceiver(), f)
        while True: sleep(10)
    except: pass