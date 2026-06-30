import sqlite3, csv, os
from datetime import datetime, timedelta
from kivy.app import App
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty, ListProperty
try: from jnius import autoclass
except: pass

KV = '''
<LogCard@BoxLayout>:
    orientation: 'horizontal'
    size_hint_y: None
    height: '110dp'
    padding: '12dp'
    spacing: '10dp'
    canvas.before:
        Color:
            # 🚧 작업 모드는 푸른빛, 🚨 상시 모드는 붉은빛 배경
            rgba: (0.92, 0.96, 1, 1) if root.mode == "작업" else (1, 0.92, 0.92, 1)
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [15]
            
    BoxLayout:
        orientation: 'vertical'
        size_hint_x: 0.75
        BoxLayout:
            size_hint_y: 0.35
            Label:
                text: f"{root.worker_name}"
                font_size: '18sp'
                color: 0.1, 0.1, 0.1, 1
                bold: True
                text_size: self.size
                halign: 'left'
                valign: 'middle'
            Label:
                text: f"[{root.mode}]"
                font_size: '13sp'
                color: (0.1, 0.4, 0.8, 1) if root.mode == "작업" else (0.8, 0.1, 0.1, 1)
                bold: True
                text_size: self.size
                halign: 'right'
                valign: 'middle'
        Label:
            text: f"📍 {root.project}  |  출입: {root.in_time} / 퇴실: {root.out_time}"
            font_size: '13sp'
            color: 0.3, 0.3, 0.3, 1
            bold: True
            text_size: self.size
            halign: 'left'
            valign: 'middle'
            size_hint_y: 0.35
        Label:
            text: f"📝 {root.task_reason} | 🏥 {root.health}"
            font_size: '12sp'
            color: (0.8, 0.2, 0.2, 1) if ("고혈압" in root.health or "당뇨" in root.health or "심혈관" in root.health) else (0.4, 0.4, 0.4, 1)
            bold: True
            text_size: self.size
            halign: 'left'
            valign: 'middle'
            shorten: True
            size_hint_y: 0.3
            
    BoxLayout:
        orientation: 'vertical'
        size_hint_x: 0.25
        spacing: '8dp'
        Button:
            text: '이수증/사진'
            background_normal: ''
            background_color: 0.2, 0.6, 0.3, 1
            font_size: '12sp'
            bold: True
            disabled: root.photo_path == "" or root.photo_path == "사진없음"
            on_release: app.open_photo(root.photo_path)
        Button:
            text: '기록 삭제'
            background_normal: ''
            background_color: 0.8, 0.3, 0.3, 1
            font_size: '12sp'
            bold: True
            on_release: app.delete_log(root.log_id)

BoxLayout:
    orientation: 'vertical'
    padding: '12dp'
    spacing: '12dp'
    canvas.before:
        Color:
            rgba: 0.95, 0.95, 0.97, 1
        Rectangle:
            pos: self.pos
            size: self.size

    # 📅 타임머신 네비게이터
    BoxLayout:
        size_hint_y: 0.08
        spacing: '10dp'
        Button:
            text: '◀ 이전일'
            size_hint_x: 0.25
            background_normal: ''
            background_color: 0.2, 0.3, 0.4, 1
            font_size: '14sp'
            bold: True
            on_release: app.change_date(-1)
        Label:
            text: app.current_display_date
            size_hint_x: 0.5
            font_size: '20sp'
            bold: True
            color: 0.1, 0.1, 0.1, 1
        Button:
            text: '다음일 ▶'
            size_hint_x: 0.25
            background_normal: ''
            background_color: 0.2, 0.3, 0.4, 1
            font_size: '14sp'
            bold: True
            on_release: app.change_date(1)

    # 🔍 스마트 필터
    BoxLayout:
        size_hint_y: 0.08
        spacing: '8dp'
        Spinner:
            id: project_spinner
            text: '전체 현장'
            values: app.project_list
            background_normal: ''
            background_color: 1, 1, 1, 1
            color: 0.1, 0.1, 0.1, 1
            font_size: '14sp'
            bold: True
            on_text: app.refresh()
        Spinner:
            id: mode_spinner
            text: '모드: 전체'
            values: ['모드: 전체', '모드: 작업', '모드: 상시']
            background_normal: ''
            background_color: 1, 1, 1, 1
            color: 0.1, 0.1, 0.1, 1
            font_size: '14sp'
            bold: True
            on_text: app.refresh()

    ScrollView:
        size_hint_y: 0.74
        BoxLayout:
            id: log_list
            orientation: 'vertical'
            size_hint_y: None
            height: self.minimum_height
            spacing: '10dp'
            
    Button:
        size_hint_y: 0.1
        text: '현재 표시된 날짜 CSV (엑셀) 추출'
        background_normal: ''
        background_color: 0.1, 0.5, 0.8, 1
        font_size: '16sp'
        bold: True
        on_release: app.export_excel()
'''

class MasterDashboardApp(App):
    current_display_date = StringProperty("")
    project_list = ListProperty(['전체 현장'])
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.target_date_obj = datetime.now()

    def build(self):
        self.conn = sqlite3.connect("master_attendance.db")
        self.root = Builder.load_string(KV)
        self.update_date_text()
        self.start_service()
        # 3초마다 DB 변경사항을 감지하여 자동 새로고침
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
        self.conn.commit(); self.refresh()

    def refresh(self):
        date_str = self.current_display_date
        cur = self.conn.cursor()
        
        # 필터링용 현장 리스트 갱신
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