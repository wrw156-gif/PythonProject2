import sqlite3, csv, os
from datetime import datetime, timedelta
from kivy.app import App
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty, ListProperty

# 💡 [핵심] Kivy 기본 폰트를 한글 폰트(font.ttf)로 강제 교체!
from kivy.core.text import LabelBase
LabelBase.register(name='Roboto', fn_regular='font.ttf')

try: 
    from jnius import autoclass
except: 
    pass

KV = '''
#:import utils kivy.utils

<ModernButton@ButtonBehavior+Label>:
    bg_color: 0.5, 0.5, 0.5, 1
    bg_color_pressed: 0.3, 0.3, 0.3, 1
    canvas.before:
        Color:
            rgba: self.bg_color if self.state == 'normal' else self.bg_color_pressed
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [14]
    color: 1, 1, 1, 1
    bold: True
    font_size: '14sp'

<LogCard@BoxLayout>:
    orientation: 'horizontal'
    size_hint_y: None
    height: '140dp'
    padding: '20dp'
    spacing: '16dp'
    canvas.before:
        Color:
            rgba: 1, 1, 1, 1
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [24]
        Color:
            rgba: utils.get_color_from_hex('#007AFF') if root.mode == "작업" else utils.get_color_from_hex('#FF3B30')
        RoundedRectangle:
            pos: self.pos[0], self.pos[1]
            size: 8, self.size[1]
            radius: [24, 0, 0, 24]

    BoxLayout:
        orientation: 'vertical'
        size_hint_x: 0.75
        spacing: '6dp'
        BoxLayout:
            size_hint_y: None
            height: '24dp'
            Label:
                text: f"{root.worker_name}"
                font_size: '20sp'
                color: utils.get_color_from_hex('#1C1C1E')
                bold: True
                text_size: self.size
                halign: 'left'
                valign: 'middle'
            Label:
                text: f"[{root.mode}]"
                font_size: '13sp'
                color: utils.get_color_from_hex('#007AFF') if root.mode == "작업" else utils.get_color_from_hex('#FF3B30')
                bold: True
                text_size: self.size
                halign: 'right'
                valign: 'middle'
        Label:
            text: f"📍 {root.project}"
            font_size: '14sp'
            color: utils.get_color_from_hex('#8E8E93')
            bold: True
            text_size: self.size
            halign: 'left'
            valign: 'middle'
            size_hint_y: None
            height: '20dp'
        Label:
            text: f"🕒 출입: {root.in_time}  |  퇴실: {root.out_time}"
            font_size: '13sp'
            color: utils.get_color_from_hex('#3A3A3C')
            bold: True
            text_size: self.size
            halign: 'left'
            valign: 'middle'
            size_hint_y: None
            height: '18dp'
        Label:
            text: f"📝 {root.task_reason}  |  🏥 {root.health}"
            font_size: '13sp'
            color: utils.get_color_from_hex('#FF3B30') if ("고혈압" in root.health or "당뇨" in root.health or "심혈관" in root.health) else utils.get_color_from_hex('#8E8E93')
            bold: True
            text_size: self.size
            halign: 'left'
            valign: 'middle'
            shorten: True
            shorten_from: 'right'

    BoxLayout:
        orientation: 'vertical'
        size_hint_x: 0.25
        spacing: '10dp'
        padding: [0, '4dp', 0, '4dp']
        ModernButton:
            text: '사진확인'
            bg_color: utils.get_color_from_hex('#34C759')
            bg_color_pressed: utils.get_color_from_hex('#28A745')
            opacity: 0.4 if (root.photo_path == "" or root.photo_path == "사진없음") else 1.0
            disabled: root.photo_path == "" or root.photo_path == "사진없음"
            on_release: app.open_photo(root.photo_path)
        ModernButton:
            text: '삭제'
            bg_color: utils.get_color_from_hex('#FF3B30')
            bg_color_pressed: utils.get_color_from_hex('#D70015')
            on_release: app.delete_log(root.log_id)

BoxLayout:
    orientation: 'vertical'
    padding: '20dp'
    spacing: '20dp'
    canvas.before:
        Color:
            rgba: utils.get_color_from_hex('#F2F2F7')
        Rectangle:
            pos: self.pos
            size: self.size

    BoxLayout:
        size_hint_y: None
        height: '60dp'
        spacing: '12dp'
        padding: '8dp'
        canvas.before:
            Color:
                rgba: 1, 1, 1, 1
            RoundedRectangle:
                pos: self.pos
                size: self.size
                radius: [20]
        ModernButton:
            text: '◀'
            size_hint_x: 0.2
            bg_color: utils.get_color_from_hex('#E5E5EA')
            bg_color_pressed: utils.get_color_from_hex('#D1D1D6')
            color: utils.get_color_from_hex('#1C1C1E')
            on_release: app.change_date(-1)
        Label:
            text: app.current_display_date
            size_hint_x: 0.6
            font_size: '22sp'
            bold: True
            color: utils.get_color_from_hex('#1C1C1E')
        ModernButton:
            text: '▶'
            size_hint_x: 0.2
            bg_color: utils.get_color_from_hex('#E5E5EA')
            bg_color_pressed: utils.get_color_from_hex('#D1D1D6')
            color: utils.get_color_from_hex('#1C1C1E')
            on_release: app.change_date(1)

    BoxLayout:
        size_hint_y: None
        height: '48dp'
        spacing: '12dp'
        Spinner:
            id: project_spinner
            text: '전체 현장'
            values: app.project_list
            background_normal: ''
            background_color: 1, 1, 1, 1
            color: utils.get_color_from_hex('#1C1C1E')
            font_size: '15sp'
            bold: True
            on_text: app.refresh()
            canvas.before:
                Color:
                    rgba: 1, 1, 1, 1
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [14]
        Spinner:
            id: mode_spinner
            text: '모드: 전체'
            values: ['모드: 전체', '모드: 작업', '모드: 상시']
            background_normal: ''
            background_color: 1, 1, 1, 1
            color: utils.get_color_from_hex('#1C1C1E')
            font_size: '15sp'
            bold: True
            on_text: app.refresh()
            canvas.before:
                Color:
                    rgba: 1, 1, 1, 1
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [14]

    ScrollView:
        size_hint_y: 1
        BoxLayout:
            id: log_list
            orientation: 'vertical'
            size_hint_y: None
            height: self.minimum_height
            spacing: '16dp'
            padding: [0, '4dp', 0, '20dp']
            
    ModernButton:
        size_hint_y: None
        height: '60dp'
        text: '현재 표시된 날짜 CSV (엑셀) 추출'
        font_size: '18sp'
        bg_color: utils.get_color_from_hex('#007AFF')
        bg_color_pressed: utils.get_color_from_hex('#0056B3')
        on_release: app.export_excel()
'''

class MasterDashboardApp(App):
    current_display_date = StringProperty("")
    project_list = ListProperty(['전체 현장'])
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.target_date_obj = datetime.now()

    def init_db(self):
        self.conn = sqlite3.connect("master_attendance.db")
        self.conn.execute('''CREATE TABLE IF NOT EXISTS logs 
                        (id INTEGER PRIMARY KEY, date TEXT, mode TEXT, proj TEXT, name TEXT, 
                         phone TEXT, in_t TEXT, out_t TEXT, task_reason TEXT, health TEXT, photo TEXT)''')
        self.conn.commit()

    def build(self):
        self.init_db() 
        self.root = Builder.load_string(KV)
        self.update_date_text()
        self.start_service()
        Clock.schedule_interval(lambda dt: self.refresh(), 3.0)
        return self.root

    def start_service(self):
        try:
            mActivity = autoclass('org.kivy.android.PythonActivity').mActivity
            service = autoclass(str(mActivity.getApplicationContext().getPackageName()) + '.ServiceSmsservice')
            service.start(mActivity, '')
        except: pass

    def update_date_text(self):
        self.current_display_date = self.target_date_obj.strftime("%Y-%m-%d")
        self.refresh()

    def change_date(self, days):
        self.target_date_obj += timedelta(days=days)
        self.update_date_text()

    def open_photo(self, path):
        try:
            from android import mActivity
            Intent = autoclass('android.content.Intent')
            Uri = autoclass('android.net.Uri')
            File = autoclass('java.io.File')
            intent = Intent(Intent.ACTION_VIEW)
            intent.setDataAndType(Uri.fromFile(File(path)), "image/*")
            mActivity.startActivity(intent)
        except: pass

    def delete_log(self, log_id):
        self.conn.execute("DELETE FROM logs WHERE id=?", (log_id,))
        self.conn.commit()
        self.refresh()

    def refresh(self):
        date_str = self.current_display_date
        cur = self.conn.cursor()
        
        cur.execute("SELECT DISTINCT proj FROM logs WHERE date=?", (date_str,))
        self.project_list = ['전체 현장'] + [row[0] for row in cur.fetchall()]

        selected_proj = self.root.ids.project_spinner.text
        selected_mode = self.root.ids.mode_spinner.text

        query = "SELECT id, mode, proj, name, phone, in_t, out_t, task_reason, health, photo FROM logs WHERE date=?"
        params = [date_str]

        if selected_proj != '전체 현장':
            query += " AND proj=?"; params.append(selected_proj)
        if selected_mode == '모드: 작업':
            query += " AND mode='작업'"
        elif selected_mode == '모드: 상시':
            query += " AND mode='상시'"

        query += " ORDER BY id DESC"
        rows = cur.execute(query, tuple(params)).fetchall()

        log_list = self.root.ids.log_list
        log_list.clear_widgets()
        
        from kivy.factory import Factory
        for r in rows:
            item = Factory.LogCard()
            item.log_id = r[0]; item.mode = r[1]; item.project = r[2]; item.worker_name = r[3]
            item.phone = r[4]; item.in_time = r[5] or "-"; item.out_time = r[6] or "-"
            item.task_reason = r[7] or "-"; item.health = r[8] or "해당없음"; item.photo_path = r[9] or ""
            log_list.add_widget(item)

    def export_excel(self):
        date_str = self.current_display_date
        save_dir = "/storage/emulated/0/Download/"
        if not os.path.exists(save_dir): return
        
        filepath = f"{save_dir}출입현황_{date_str}.csv"
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(['ID', '수신일자', '모드', '장소', '이름', '발신폰번호', '출입시각', '퇴실시각', '공정/사유', '건강상태', '사진경로'])
            writer.writerows(self.conn.execute("SELECT * FROM logs WHERE date=? ORDER BY mode, proj, in_t", (date_str,)).fetchall())

if __name__ == '__main__': MasterDashboardApp().run()