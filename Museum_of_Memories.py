import os
from sys import argv

import pygame
from PIL import Image,ImageTk
import ctypes
import threading
import queue
import random
import time
import webbrowser
from collections import Counter
from datetime import datetime

import tkinter as tk
from tkinter import filedialog,messagebox,PhotoImage,ttk
from tkinter.constants import *

# グローバル変数
#cwd = os.path.dirname(__file__) # exe化した際は一時ファイルの方のpyファイルのディレクトリ
#dir_name = os.path.dirname(os.path.abspath(argv[0])) # exe化した際は実行している方のファイルのディレクトリ

map_canvas = None
animation_running = True
restart_flg = False
image_queue = queue.Queue() # グローバル変数として選択された画像のフルパスを保持するためのキュー
#=====================================================================
def Pygame_thread():
    # 別スレッドを立ててPygameの画面とメイン画面を個別に動かす
    # メイン処理を動かす前にアニメーションは消しておく
    stop_animation()

    try:
        thread_main = threading.Thread(target = Map_Create_Process)
        thread_main.start()
    except Exception as e:
        messagebox.showerror("エラー発生", f"想定外のエラーが発生しました\n このエラーを直してほしいなぁって…\n\n{str(e)}")

def Map_Create_Process():
    #pygame画面は同時に一つまでしか表示できないため，既存の画面起動中は押させないようにする．
    button6.config(state=tk.DISABLED)
    
    # 初期化
    pygame.init()

    root = tk.Tk()
    root.withdraw()  # メインのTkinterウィンドウを隠す

    # 画面サイズの設定
    selection = combo1.get()
    screen_width = 0   # スクリーンの幅
    screen_height = 0  # スクリーンの高さ
    
    button_size = 3    # ボタン大きさの倍率
    Base_x_state = 520 # ボタンの配置基準位置

    pause_size = 2     # pause3ページ目の画像大きさ倍率
    pause_x_state = 5  # pause3ページ目の画像配置（横）
    pause_y_state = 40 # pause3ページ目の画像配置（縦）

    if selection == "フルスクリーン":
        screen_width, screen_height = get_screen_resolution()
        pause_size = 4
        pause_y_state = 65
    elif selection ==  "スマホ画面":
        screen_width = 416
        screen_height = 699 
        button_size = 4
        Base_x_state = 310
        pause_size = 1.5
        pause_y_state = 20
    elif selection ==  "はがき・ポスカ":
        screen_width = 480
        screen_height = 720
        button_size = 4.2
        Base_x_state = 385
        pause_size = 1.5
        pause_y_state = 20
    elif selection ==  "1020x690":
        screen_width = 1020
        screen_height = 690
    else:
        screen_width = 704
        screen_height = 544
    
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Museum of Memories -Exhibition hall-")

    # アイコン画像の読み込みと設定
    icon_path = os.path.join(os.path.dirname(__file__),'exe_logo.ico')
    icon_image = pygame.image.load(icon_path)
    pygame.display.set_icon(icon_image)

    # スプライトシートとマップの読み込み
    Get_CharaImage = textbox2.get("1.0", "end-1c")
    sprite_sheet = pygame.image.load(Get_CharaImage).convert_alpha()

    # 画像の幅を確認し、必要に応じてリサイズ
    original_width, original_height = sprite_sheet.get_size()

    if original_width > 96:
        # 96pixelより幅がある場合は縦横比を保持しつつ幅を96ピクセルにリサイズ
        aspect_ratio = original_height / original_width
        new_height = int(96 * aspect_ratio)
        sprite_sheet = pygame.transform.smoothscale(sprite_sheet, (96, new_height))

    Get_MapImage = textbox1.get("1.0", "end-1c")
    map_image = pygame.image.load(Get_MapImage).convert()
    
    # 画像の幅と高さを取得
    map_width, map_height = map_image.get_size()

    #----------------------------------------------------------------------------------------
    # Hidden_image配置設定
    Simple_flg = label8.cget("text") # 白い画面で簡単に実行されることを防ぐためのフラグ
    
    # 画像の横幅が1900未満，画像の高さが1600未満，画像を占める同じ色の数が一定割合を超えるシンプル画像の場合はお尋ね者がでなくなるフラグ
    if (map_width < 1900 and map_height < 1600) or Simple_flg == 1:
        Moo_hidden_flg = True # 隠れムゥちゃんでない
    else:
        Moo_hidden_flg = False # 隠れムゥちゃん出現

    if Moo_hidden_flg == False:
        CH_Randomizer = random.randint(0,3)
        
        image_path = os.path.join(os.path.dirname(__file__),'image',f"Secret_image_{CH_Randomizer}.png")
        random_image = pygame.image.load(image_path).convert_alpha()
        SecretCH_width = random_image.get_width()
        SecretCH_height = random_image.get_height()
        
        random_x = random.randint(0, map_width - SecretCH_width)
        random_y = random.randint(0, map_height - SecretCH_height)
        
        hidden_character_start_time = time.time()  # タイマー開始
    else:
        #Hidden_imageが非表示の反千絵になった際はブランクを画面の端に表示する
        image_path = os.path.join(os.path.dirname(__file__),'image',"Blank_image.png")
        random_image = pygame.image.load(image_path).convert_alpha()
        SecretCH_width = 1
        SecretCH_height = 1
        
        random_x = 0
        random_y = 0    

    #----------------------------------------------------------------------------------------
    # キャラクターの設定
    CHARACTER_SIZE = 32
    ANIMATION_FRAMES = 3
    DIRECTIONS = {'down': 0, 'left': 1, 'right': 2, 'up': 3}
    direction = 'down'
    frame = 0
    frame_increment = 1
    
    # アニメーションフレーム制御
    frame_count = 0
    frame_repeat = 3  # 各フレームを3回繰り返す
    
    character_x, character_y = map_width // 2, map_height // 2

    # 画面の初期表示領域を画像の中央に設定
    scroll_x = (map_width - screen_width) // 2
    scroll_y = (map_height - screen_height) // 2

    # クロックの設定
    clock = pygame.time.Clock()

    # 別スレッドに渡すキューの設定
    close_queue = queue.Queue()

    # CHスプライトの取得
    def get_character_sprite(direction, frame):
        row = DIRECTIONS[direction]
        col = frame % ANIMATION_FRAMES
        return sprite_sheet.subsurface(col * CHARACTER_SIZE, row * CHARACTER_SIZE, CHARACTER_SIZE, CHARACTER_SIZE)

    #----------------------------------------------------------------------------------------]
    # ボタン画像の配置処理
    button_paths = [
    'Pause_button1.png',  # 操作説明
    'Pause_button2.png',  # スクリーンショット撮影
    'Pause_button3.png',  # 画面に素材を配置
    'Pause_button4.png',  # 素材配置をリセット
    'Pause_button5.png'   # 秘密の暗号
    ]

    buttons = []  # ボタン情報を保存するリスト
    for i, button_filename in enumerate(button_paths):
        button_path = os.path.join(os.path.dirname(__file__), 'image', button_filename)
        button_image = pygame.image.load(button_path).convert_alpha()

        # ボタンをリサイズして位置を設定
        button_width, button_height = button_image.get_size()
        button_width = button_width // button_size
        button_height = button_height // button_size
        button_image = pygame.transform.scale(button_image, (button_width, button_height))

        # ボタンの位置設定
        if i == 0:
            button_x = screen_width - button_width - Base_x_state  # 最初のボタンのみ左端に配置
        else:
            button_x = buttons[-1]['rect'].right + 10  # 右隣に配置

        button_y = screen_height - button_height - 10
        button_rect = pygame.Rect(button_x, button_y, button_width, button_height)

        # ボタン情報をリストに保存
        buttons.append({
            'image': button_image,
            'rect': button_rect
        })

    #----------------------------------------------------------------------------------------
    show_instructions = False #pause画面表示/非表示を制御するフラグ
    show_buttons = True  # ボタンの表示/非表示を制御するフラグ
    show_transparent_image = True # スタンプ機能を使用するかの制御フラグ
    image_selection_window_open = False # 画像一覧選択ウィンドウが表示されたの制御フラグ
        
    # 画像クリック時のクリック座標
    mouse_x = 0
    mouse_y = 0

    # Undo/Redo用のスタック
    undo_stack = []
    redo_stack = []
    stamped_images = []
    
    # フェードインの設定
    fade_in_duration = 3  # フェードインの持続時間（秒）
    fade_in_start_time = pygame.time.get_ticks()  # フェードインの開始時間
    fade_in_surface = pygame.Surface((screen_width, screen_height))
    fade_in_surface.fill((255, 255, 255))

    # マウスカーソルに表示する画像
    selected_image = None
    selected_image_surface = None    
    image_flipped = False # 画像の左右反転フラグ
    
    # 画面上に表示するフォントの設定
    font_path = r"C:\Windows\Fonts\YuGothM.ttc"
    font = pygame.font.Font(font_path, 14)
    #---------------------------------------------------------------
    def take_screenshot():
        #スクリーンショットの処理
        nonlocal show_buttons
        show_buttons = False  # ボタンを一時的に非表示

        # 画面を更新してボタンを消す
        screen.fill((0, 0, 0))  # 画面をクリア
        screen.blit(map_image, (0, 0), (scroll_x, scroll_y, screen_width, screen_height))

        # スタンプした画像を再描画
        for image, (map_x, map_y) in stamped_images:
                screen_x = map_x - scroll_x
                screen_y = map_y - scroll_y
                screen.blit(image, (screen_x, screen_y))
                
        # 隠れムゥちゃんを再描画
        screen.blit(random_image, (random_x - scroll_x, random_y - scroll_y))

        #CH画像を再描画
        character_sprite = get_character_sprite(direction, frame)
        screen.blit(character_sprite, (character_x - scroll_x - 16, character_y - scroll_y - 16))

        # 画面右下に撮影時の文字を描画
        now_time = datetime.now().strftime("%Y.%m.%d_%H.%M.%S")
        mode_text = font.render(f"{now_time}_Picture by Museum of Memories", True, (0,0,0))
        text_rect = mode_text.get_rect()
        text_rect.bottomright = (screen.get_width() - 10, screen.get_height() - 10) # 白四角を記載する

        # 半分透過した白い四角を描画
        overlay = pygame.Surface((text_rect.width + 20, text_rect.height + 10))  # 四角のサイズを文字に合わせる
        overlay.set_alpha(128)  # 透過度を設定（0から255、128は半分透過）
        overlay.fill((255, 255, 255))  # 白で塗りつぶす
        screen.blit(overlay, (text_rect.x - 10, text_rect.y - 5))  # 四角を描画
        
        screen.blit(mode_text, (screen.get_width() - mode_text.get_width() - 10, screen.get_height() - mode_text.get_height() - 10)) # テキストを表示
        pygame.display.flip()  # 画面を更新

        # スクリーンショットを撮る
        screenshot = screen.copy()

        #このファイルのある場所（作成済みファイルを移動するのに使うので）
        filename = (f"screenshot_{now_time}.png")
        dir_name = os.path.dirname(os.path.abspath(argv[0]))  + '\\' + filename
        pygame.image.save(screenshot, dir_name)        
        messagebox.showinfo("保存完了", "この画面を記念撮影しました")
        
        show_buttons = True  # ボタンを再表示
    #---------------------------------------------------------------
    # スタンプ選択ウィンドウ処理
    def open_image_thread():
        # 別スレッドを立ててPygameの画面とメイン画面を個別に動かす
        # 既に画像選択ウィンドウが開かれている場合は新しいウィンドウを開かない
        if not image_selection_window_open:
            image_thread = threading.Thread(target=open_image_selection, args=(close_queue,))
            image_thread.start()

    def open_image_selection(close_queue):
        try:
            root = tk.Tk()
            root.withdraw()  # Hide the root window

            nonlocal image_selection_window_open
            image_selection_window_open = True  # ウィンドウが開かれていることを示す

            dir_name = os.path.dirname(os.path.abspath(argv[0]))
            images_folder = os.path.join(dir_name, 'Materials')
            
            subfolders = [f for f in os.listdir(images_folder) if os.path.isdir(os.path.join(images_folder, f))]

            def on_image_click(event, img_path):
                try:
                    image_queue.put(img_path)  # キューに画像パスを追加
                    hwnd = pygame.display.get_wm_info()['window']
                    ctypes.windll.user32.ShowWindow(hwnd, 9)  # SW_RESTORE: 通常表示に戻す

                    # 一定回数までフォーカスを試みるループ（成功するまでリトライ）
                    max_retries = 20  # 最大リトライ回数                    
                    for _ in range(max_retries):
                        # ウィンドウを最前面に持ってくる
                        ctypes.windll.user32.BringWindowToTop(hwnd)
                        ctypes.windll.user32.SetForegroundWindow(hwnd)
                        ctypes.windll.user32.SetFocus(hwnd)
                        ctypes.windll.user32.SetActiveWindow(hwnd)
                        
                        # 現在のフォーカスが自分のウィンドウに設定されているか確認
                        if ctypes.windll.user32.GetForegroundWindow() == hwnd:
                            break

                except:
                    messagebox.showerror("素材選択エラー", "マップ画面がない状態で素材を選択することはできません\nマップ画面を読込直してから選択してください")

            def on_window_close():
                nonlocal image_selection_window_open
                image_selection_window_open = False  # フラグをリセットしてウィンドウが閉じられたことを示す
                root.destroy()

            selection_window = tk.Toplevel(root)
            selection_window.title("Museum of Memories -Buck stage-")
            selection_window.protocol("WM_DELETE_WINDOW", on_window_close)  # ウィンドウが閉じられたときの処理

            # Canvasを作成してスクロールバーを有効に
            canvas = tk.Canvas(selection_window)
            scrollbar = ttk.Scrollbar(selection_window, orient="vertical", command=canvas.yview)
            scrollable_frame = tk.Frame(canvas)

            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )

            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)

            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")

            # マウスホイールのスクロール対応
            def on_mouse_wheel(event):
                if event.delta:  # Windows用
                    canvas.yview_scroll(-1 * int(event.delta / 120), "units")
                else:  # macOS用
                    canvas.yview_scroll(-1 * int(event.delta), "units")

            # マウスホイールイベントをCanvasにバインド
            canvas.bind_all("<MouseWheel>", on_mouse_wheel)  # Windows/Linux
            canvas.bind_all("<Button-4>", on_mouse_wheel)  # Linuxでのスクロール対応
            canvas.bind_all("<Button-5>", on_mouse_wheel)  # Linuxでのスクロール対応

            image_refs = []

            row = 0
            main_images = [f for f in os.listdir(images_folder) if f.endswith('.png')]

            def display_images_for_folder(folder, images, row, is_main_folder=False):
                # カテゴリ名（フォルダ名）を表示
                folder_label = tk.Label(scrollable_frame, text=folder, font=('Arial', 12, 'bold'))
                folder_label.grid(row=row, column=0, columnspan=10, sticky="w")
                row += 1

                # 画像を表示
                for idx, img_file in enumerate(images):
                    # Mainフォルダかどうかで画像パスの生成方法を変える
                    if is_main_folder:
                        img_path = os.path.join(images_folder, img_file)
                    else:
                        img_path = os.path.join(images_folder, folder, img_file)

                    img = tk.PhotoImage(file=img_path, master=root)

                    ratio = 32 / img.width()
                    new_height = int(img.height() * ratio)
                    img = img.subsample(max(img.width() // 32, 1), max(img.height() // new_height, 1))  # 高さを基準にリサイズ

                    image_refs.append(img)  # 画像参照をリストに追加して保持
                    img_label = tk.Label(scrollable_frame, image=img)
                    img_label.image = img  # 画像参照を保持してガベージコレクションを防ぐ
                    img_label.grid(row=row + idx // 10, column=idx % 10)
                    img_label.bind("<Button-1>", lambda e, img_path=img_path: on_image_click(e, img_path))

                row += len(images) // 10 + 1
                return row

            # メインフォルダ内の画像を最初に表示
            if main_images:
                row = display_images_for_folder("No Categorize", main_images, row, is_main_folder=True)

            # 子フォルダの画像をそれぞれ表示
            for subfolder in subfolders:
                folder_path = os.path.join(images_folder, subfolder)
                image_files = [f for f in os.listdir(folder_path) if f.endswith('.png')]
                if image_files:
                    row = display_images_for_folder(subfolder, image_files, row)

            def check_queue():
                #一覧ウィンドウの同期処理を行い、pygameメイン画面からCLOSEのメッセージを受け取ったら子画面も削除する
                try:
                    msg = close_queue.get_nowait()
                    if msg == "CLOSE":
                        root.destroy()
                except queue.Empty:
                    pass
                root.after(100, check_queue)

            root.after(100, check_queue)
            root.mainloop()
        except:
            result = messagebox.askyesno("素材が見つかりません", "『Materials』フォルダが見つかりませんでした．\n『Materials』フォルダを新しく作成しますか？")
            if result:  # YESが選択された場合                
                folder_path = os.path.join(os.path.dirname(os.path.abspath(argv[0])), "Materials")
                os.makedirs(folder_path, exist_ok=True)
                messagebox.showinfo("作成完了", f"Materialsフォルダを新規で作成しました。")

    #---------------------------------------------------------------
    # 秘密のコードを入力画面の処理
    
    VALID_CHARACTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"  # 有効な文字（大文字アルファベットと数字）
    SECRET_CODES = {
                    "MOOMOO55": 'https://www.dropbox.com/scl/fi/d27g3ppd0zu39cx87ema3/MOOMOO55.zip?rlkey=0z0mbwc8p0eraaxbhewayk8ry&st=38zcpmh3&dl=1',
                    "FLOWERJK": 'https://www.dropbox.com/scl/fi/qjfym2g02n577ue99c0m8/FLOWERJK.zip?rlkey=k5tc5db04b0iu5kf3nmz702za&st=9w1o8nbh&dl=1',
                    "SPEEDRUN": 'https://www.dropbox.com/scl/fi/vcpaytxmfbjgw3chlnzjj/SPEEDRUN.zip?rlkey=1wriutzbl9z7epi0lwb3yr7uk&st=l0ebfdjv&dl=1',
                    "TEISATHU": 'https://www.dropbox.com/scl/fi/d3oy3k5o9gm4pzjcls5qu/TEISATHU.zip?rlkey=gebv1tj1fo89wl7xxjchh74pr&st=xrrfifkr&dl=1',
                    "KULO1997": 'https://www.dropbox.com/scl/fi/5257h4915b2dkmvfdxzfw/KULO1997.zip?rlkey=e5xuhrxt25q2z05ofeylv2120&st=126v47hm&dl=1',
                    "REPHISE0": 'https://www.dropbox.com/scl/fi/i23yb757j0tw614jypr1i/REPHISE0.zip?rlkey=wm2u6vtgun51qdmsq91brom4h&st=m09zvrge&dl=1',
                    "KANA2001": 'https://www.dropbox.com/scl/fi/l9mrcrmj4enai5eyae52u/KANA2001.zip?rlkey=isz7bt56o9f8tmopc2l9cdeh6&st=cxpquivm&dl=1',
                    "NAHATO96": 'https://www.dropbox.com/scl/fi/3bcdlwdej4xul97hf9js4/NAHATO96.zip?rlkey=oavtajkpobr03qqhb6966otct&st=nmptxxtp&dl=1'
                    }

    def show_code_input_thread():
    # 別スレッドを立ててPygameの画面とメイン画面を個別に動かす
    # 既に画像選択ウィンドウが開かれている場合は新しいウィンドウを開かない
        input_thread = threading.Thread(target=show_code_input_window, args=(close_queue,))
        input_thread.start()
    
    # Tkinterウィンドウの設定
    def show_code_input_window(close_queue):
        def on_submit():
            entered_code = ''.join(entry.get() for entry in entries)
            if entered_code in SECRET_CODES:
                webbrowser.open(SECRET_CODES[entered_code])  # 対応するURLを開く
                code_input_window.destroy()
            else:
                messagebox.showerror("コードが違うよ", "秘密の合言葉が間違っています")

        def focus_next_widget(event, current_index):
            next_index = (current_index + 1) % len(entries)
            entries[next_index].focus_set()
        
        def focus_previous_widget(event, current_index):
            next_index = (current_index - 1) % len(entries)
            entries[next_index].focus_set()
        
        code_input_window = tk.Tk()
        code_input_window.title("秘密の合言葉を入力")
        code_input_window.configure(bg=Label_color)

        entries = []
        for i in range(8):
            entry = tk.Entry(code_input_window, width=2, font=('Arial', 18), justify='center')
            entry.grid(row=0, column=i, padx=5)
            entry.bind('<KeyRelease>', lambda event, index=i: validate_char(event, index))
            entry.bind('<Return>', lambda event, index=i: focus_next_widget(event, index))
            entry.bind('<Right>', lambda event, index=i: focus_next_widget(event, index))
            entry.bind('<Left>', lambda event, index=i: focus_previous_widget(event, index))
            entries.append(entry)

        submit_button = tk.Button(code_input_window, text="合言葉を入力", command=on_submit)
        submit_button.grid(row=1, columnspan=8)
        
        def check_queue():
            #一覧ウィンドウの同期処理を行い、pygameメイン画面からCLOSEのメッセージを受け取ったら子画面も削除する
            try:
                msg = close_queue.get_nowait()
                if msg == "CLOSE":
                    code_input_window.destroy()
            except queue.Empty:
                pass
            code_input_window.after(100, check_queue)

        code_input_window.after(100, check_queue)
        code_input_window.mainloop()

    # 入力制限の設定
    def validate_char(event, index):
        char = event.widget.get()
        if len(char) > 1 or char.upper() not in VALID_CHARACTERS:
            event.widget.delete(0, tk.END)
        else:
            event.widget.delete(0, tk.END)
            event.widget.insert(0, char.upper())

    #---------------------------------------------------------------
    # pause画面の読込処理
    # 画像の横幅をウィンドウの横幅に合わせてリサイズ
    image_width = screen_width // 1.1
    
    # 画像を格納するリスト
    explanation_images = []
    
    # 読み込む画像の番号リスト
    image_numbers = [1 , 2 , 3 , 4 , 5]
    
    # 最初に表示しておく画像番号の指定
    current_explanation_page = 0
    
    for number in image_numbers:
        # 各画像を読み込み、リサイズ
        image_path = os.path.join(os.path.dirname(__file__), 'image', f'Pause_image{number}.png')
        image = pygame.image.load(image_path).convert_alpha()
        
        # 画像の高さをウィンドウ幅に合わせて計算
        image_height = int(image.get_height() * (image_width / image.get_width()))
        image = pygame.transform.scale(image, (image_width, image_height))
        
        # 説明用の画像をリストに格納
        explanation_images.append(image)

    #---------------------------------------------------------------

    # メインループ
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # pygame windowが終了した際の処理  
                close_queue.put("CLOSE")        
                running = False
            
            # キーを押した際の処理
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    show_instructions = not show_instructions
                elif event.key == pygame.K_ESCAPE:
                    running = False
                
                elif event.key == pygame.K_z and pygame.key.get_mods() & pygame.KMOD_CTRL:
                    if undo_stack:
                        redo_stack.append(stamped_images.copy())
                        stamped_images = undo_stack.pop()
                elif event.key == pygame.K_y and pygame.key.get_mods() & pygame.KMOD_CTRL:
                    if redo_stack:
                        undo_stack.append(stamped_images.copy())
                        stamped_images = redo_stack.pop()
                elif event.key == pygame.K_a:  # Aキーが押されたときの処理
                    if selected_image_surface:
                        image_flipped = not image_flipped  # フラグを切り替え
                        selected_image_surface = pygame.transform.flip(selected_image_surface, True, False)  # 画像を左右反転
                elif event.key == pygame.K_d: # Dキーを押されている間はbutton表示を無くす
                        show_buttons = False

                elif event.key == pygame.K_RIGHT:
                    if show_instructions and current_explanation_page < len(explanation_images) - 1: 
                        # 隠れムゥちゃん非表示フラグがTrueなら3をスキップして4を表示
                        if not Moo_hidden_flg:
                            if current_explanation_page == 2:
                                current_explanation_page += 2  # 2から4にスキップ
                            else:
                                current_explanation_page += 1
                        # 隠れムゥちゃん非表示フラグがFalseなら2をスキップして3を表示
                        else:
                            if current_explanation_page == 1:
                                current_explanation_page += 2  # 1から3にスキップ
                            else:
                                current_explanation_page += 1

                elif event.key == pygame.K_LEFT:
                    if show_instructions and current_explanation_page > 0:
                        # 隠れムゥちゃん非表示フラグがTrueなら4から2に戻る
                        if not Moo_hidden_flg:
                            if current_explanation_page == 4:
                                current_explanation_page -= 2  # 4から2にスキップ
                            else:
                                current_explanation_page -= 1
                        # 隠れムゥちゃん非表示フラグがFalseなら3から1に戻る
                        else:
                            if current_explanation_page == 3:
                                current_explanation_page -= 2  # 3から1にスキップ
                            else:
                                current_explanation_page -= 1

            # キーを離した際の処理
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_d:  # Dキーが離されたときの処理を追加
                    show_buttons = True  # Dキーが離されたらボタンを再表示する

            # マウスを押した際の処理 
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # 左クリック
                    mouse_x, mouse_y = event.pos  # クリックしたマウスポジションを記録
                    
                    button_clicked = False  # ボタンがクリックされたかどうかのフラグ
                    
                    # ボタンのクリックをチェック
                    for i, button in enumerate(buttons):
                        if button['rect'].collidepoint(event.pos):
                            button_clicked = True  # ボタンがクリックされたのでフラグを立てる
                            if show_buttons:
                                if i == 0:  # button1 に相当
                                    show_instructions = not show_instructions  # Pause画面の表示/非表示を切り替え
                                elif i == 1:  # button2 に相当
                                    open_image_thread()  # スタンプ貼り付け画面表示
                                elif i == 2:  # button3 に相当
                                    take_screenshot()  # スクリーンショット取得
                                elif i == 3:  # button4 に相当
                                    undo_stack.append(stamped_images.copy())  # 戻る操作用の処理
                                    stamped_images.clear()
                                    # キャラクター位置を画面中央にリセット
                                    character_x = scroll_x + screen_width // 2
                                    character_y = scroll_y + screen_height // 2
                                elif i == 4:  # button5 に相当
                                    show_code_input_thread()  # 秘密のコード入力画面表示
                            break  # ボタンがクリックされたらループを抜ける

                    # ボタンがクリックされていない場合の処理
                    if not button_clicked:
                        if within_hidden_character:
                            
                            if CH_Randomizer == 0:
                                Secret_code_text = 'MOOMOO55'
                            elif CH_Randomizer == 1:
                                Secret_code_text = 'FLOWERJK'
                            elif CH_Randomizer == 2:
                                Secret_code_text = 'SPEEDRUN'
                            elif CH_Randomizer == 3:
                                Secret_code_text = 'TEISATHU'
                            else:
                                Secret_code_text = 'TESTDESU'

                            # 隠れムゥちゃんの座標をクリックしたらmessage表示する
                            elapsed_time = time.time() - hidden_character_start_time
                            elapsed_time_message = f'画面サイズ： {selection} \n' + \
                                                    f"お尋ね者発見までのタイム！: {elapsed_time:.2f} 秒"
                            messagebox.showinfo("発見！", elapsed_time_message)
                            
                            aikotoba_message = f"秘密の合言葉：{Secret_code_text}\n" + \
                                                "メモしておいて『秘密の合言葉』に入力してみよう!"                            
                            messagebox.showinfo("秘密の合言葉をゲット!", aikotoba_message)
                        else:
                            # 素材を選択中の場合は画面に素材を張り付ける処理
                            if selected_image_surface:
                                # 現在の画面上の座標をマップ上の座標に変換
                                map_x = event.pos[0] + scroll_x - selected_image_surface.get_width() // 2
                                map_y = event.pos[1] + scroll_y - selected_image_surface.get_height() // 2

                                undo_stack.append(stamped_images.copy())

                                # 元の画像をロードして透明度を元に戻す
                                stamped_image_surface = pygame.image.load(selected_image).convert_alpha()

                                # 左右反転が適用されている場合は、再度反転する
                                if image_flipped:
                                    stamped_image_surface = pygame.transform.flip(stamped_image_surface, True, False)

                                # 画像をリストに追加（新しい素材のマップ座標を保存）
                                stamped_images.append((stamped_image_surface, (map_x, map_y)))

                if event.button == 3:  # 右クリック
                    show_transparent_image = not show_transparent_image
                    selected_image_surface = None  # 半透明画像を停止

        if not image_queue.empty():
            # 画像一覧画面から画像を選択中の場合は半透明の画像を表示する処理
            selected_image_path = image_queue.get()
            show_transparent_image = True
            selected_image = selected_image_path
            selected_image_surface = pygame.image.load(selected_image_path).convert_alpha()
            selected_image_surface.set_alpha(128)  # 半透明に設定
            if image_flipped:  # フラグがTrueの場合は左右反転
                selected_image_surface = pygame.transform.flip(selected_image_surface, True, False)

        # ボタンの上に乗った際だけマウスカーソルの形状を変更する処理
        mouse_pos = pygame.mouse.get_pos()
        Hidden_mouse_x, Hidden_mouse_y = mouse_pos
        within_hidden_character = (random_x <= Hidden_mouse_x + scroll_x < random_x + SecretCH_width and random_y <= Hidden_mouse_y + scroll_y < random_y + SecretCH_height)
        if show_buttons and (any(button['rect'].collidepoint(mouse_pos) for button in buttons) or within_hidden_character):
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
        else:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
        
        # キャラクターを動かしているかの判定フラグ
        is_moving = False
        frame_repeat = 3 # アニメーション速度を通常に戻す
        
        if not show_instructions:
            MoveSpeed = 6
            map_scroll_lock = False
            keys = pygame.key.get_pressed()
            if keys[pygame.K_z]:
                MoveSpeed *= 2  #Zキーを押したら移動速度↑
                frame_repeat = 2 # アニメーション速度を早くする
                
            if keys[pygame.K_x]:
                MoveSpeed //= 3 #Xキーを押したら移動速度↓
                frame_repeat = 4 # アニメーション速度を遅くする
            
            if keys[pygame.K_c]:
                map_scroll_lock = True #Cキーを押したらスクロールをロック            

            if keys[pygame.K_DOWN]:
                direction = 'down'
                if character_y < map_height - CHARACTER_SIZE:
                    character_y += MoveSpeed
                    is_moving = True
                if not map_scroll_lock and character_y > (screen_height // 2) and scroll_y < map_height - screen_height:
                    scroll_y += MoveSpeed
                    
            elif keys[pygame.K_UP]:
                direction = 'up'
                if character_y > 0:
                    character_y -= MoveSpeed
                    is_moving = True
                if not map_scroll_lock and character_y < (map_height - screen_height // 2) and scroll_y > 0:
                    scroll_y -= MoveSpeed

            elif keys[pygame.K_LEFT]:
                direction = 'left'
                if character_x > 0:
                    character_x -= MoveSpeed
                    is_moving = True
                if not map_scroll_lock and character_x < (map_width - screen_width // 2) and scroll_x > 0:
                    scroll_x -= MoveSpeed # 画面端に着いたときにスクロールを止める処理

            elif keys[pygame.K_RIGHT]:
                direction = 'right'
                if character_x < map_width - CHARACTER_SIZE:
                    character_x += MoveSpeed
                    is_moving = True
                if not map_scroll_lock and character_x > (screen_width // 2) and scroll_x < map_width - screen_width:
                    scroll_x += MoveSpeed # 画面端に着いたときにスクロールを止める処理
            
            # フレームインクリメントの制御
            if is_moving:
                frame_count += 1
                if frame_count >= frame_repeat:
                    frame_count = 0
                    frame += frame_increment

                    if frame >= ANIMATION_FRAMES - 1:
                        frame_increment = -1
                    elif frame <= 0:
                        frame_increment = 1

            # 画面の更新
            screen.fill((0, 0, 0))
            screen.blit(map_image, (0, 0), (scroll_x, scroll_y, screen_width, screen_height))
            # 隠れムゥちゃん画像をランダムな位置に描画
            screen.blit(random_image, (random_x - scroll_x, random_y - scroll_y))

            for image, (map_x, map_y) in stamped_images:
                screen_x = map_x - scroll_x
                screen_y = map_y - scroll_y
                screen.blit(image, (screen_x, screen_y))
                #screen.blit(image, pos)

            #スタンプ選択がされている場合は画面に張り付けする
            if show_transparent_image and selected_image_surface:
                screen.blit(selected_image_surface, (mouse_pos[0] - selected_image_surface.get_width() // 2, mouse_pos[1] - selected_image_surface.get_height() // 2))

            #画面でのCH画像表示位置座標
            character_sprite = get_character_sprite(direction, frame)
            screen.blit(character_sprite, (character_x - scroll_x - 16, character_y - scroll_y - 16))

            # フェードインの処理
            elapsed_time = (pygame.time.get_ticks() - fade_in_start_time) / 1000.0
            if elapsed_time < fade_in_duration:
                alpha = int((1 - elapsed_time / fade_in_duration) * 255)
                fade_in_surface.set_alpha(alpha)
                screen.blit(fade_in_surface, (0, 0))

            if show_buttons:
                # ボタンの描画
                for button in buttons:
                    screen.blit(button['image'], button['rect'].topleft)

        else:
            # 描画時
            if show_instructions:
                # pause画面表示時に画面を暗くする
                screen.blit(map_image, (0, 0), (scroll_x, scroll_y, screen_width, screen_height))
                dark_overlay = pygame.Surface((screen_width, screen_height))
                dark_overlay.set_alpha(128)
                dark_overlay.fill((0, 0, 0))
                screen.blit(dark_overlay, (0, 0))

                # 表示する画像の設定
                explanation_image = explanation_images[current_explanation_page]
                image_x = (screen_width - explanation_image.get_width()) // 2
                image_y = (screen_height - explanation_image.get_height()) // 2
                screen.blit(explanation_image, (image_x, image_y))
                
                # current_explanation_pageが3の場合は表示
                if current_explanation_page == 2:
                    explanation_image = explanation_images[current_explanation_page]
                    # 画像を2倍の大きさにスケール
                    enlarged_image = pygame.transform.scale(random_image, 
                                                            (random_image.get_width() * pause_size, 
                                                            random_image.get_height() * pause_size))
                    
                    image_x = (screen_width - enlarged_image.get_width()) // 2
                    image_y = (screen_height - enlarged_image.get_height()) // 2
                    screen.blit(enlarged_image, (image_x - pause_x_state , image_y + pause_y_state))        
                    
            if show_buttons:
                # ボタンの描画
                for button in buttons:
                    screen.blit(button['image'], button['rect'].topleft)

        pygame.display.flip()
        clock.tick(30)

    pygame.quit()
    button6.config(state=tk.NORMAL)
#======================================================================================================
def Make_DiologPath():
    #try:
        if __name__ == "__main__":
            #----------------------------------------------------------------------        
            # ファイルダイアログを表示し、ビデオファイルを選択
            global get_path
            get_path = filedialog.askopenfilename(filetypes=[("image Files", "*.png ,*.jpeg ,*.bmp ,*.gif"),("Any Files", "*.*"),])

            if get_path == "":  # ファイルが選択されなかった場合はキャンセル処理に分岐
                #messagebox.showinfo("処理キャンセル", "キャンセルされたため終了します")
                return
            #----------------------------------------------------------------------
            return (get_path)
        else:
            return()

def Get_MapImage_path():
    global map_canvas,width, height  # グローバルのキャンバス変数を使用する

    MapImage_path = Make_DiologPath()
    
    if MapImage_path == None:
        return #ダイアログ選択をキャンセルした場合
    
    textbox1.delete("1.0", tk.END)# 既存のテキストを削除
    textbox1.insert(tk.END,MapImage_path) #文字列更新
    #threading.Thread(target=Make_DiologPath).start()
    
    try:
        canvas.destroy() # 初期表示の四角形を消す
        
        with Image.open(MapImage_path) as img:
            width, height = img.size
            label5.config(text=f"横幅：{width}",justify='left')
            label6.config(text=f"縦幅：{height}",justify='left')

            # 高さ200を基準として幅を計算する
            new_width = int((width / height) * 160)
            new_image = img.resize((new_width, 160), Image.Resampling.LANCZOS)
            new_photo = ImageTk.PhotoImage(new_image)

            # 新しいキャンバスを作成して画像を表示する
            new_canvas = tk.Canvas(window, width=new_width, height=160)
            new_canvas.create_image(0, 0, anchor=tk.NW, image=new_photo)
            new_canvas.place(x=310, y=40)
            new_canvas.photo = new_photo  # ガベージコレクションの防止

            # 縮小画像からピクセルデータを取得して、単調な画像化を判断する
            pixels = list(new_image.getdata()) 
            total_pixels = len(pixels)    # 総pixel数をカウント
            color_count = Counter(pixels) # 色をコレクション

            # 最も多く出現する色の割合を計算
            most_common_color, most_common_count = color_count.most_common(1)[0]
            most_common_ratio = most_common_count / total_pixels
            if most_common_ratio > 0.5:
                label8.config(text="1",justify='left')
            else:
                label8.config(text="0",justify='left')

            # 古いキャンバスが存在する場合、削除する
            if map_canvas:
                map_canvas.destroy()

            # 新しいキャンバスをグローバル変数に代入
            map_canvas = new_canvas

            #マップとキャラ何方も入力済みなら開始ボタンを起動
            check_text_fields3()

            #キャンバスの長さに対応して横幅を変える
            if new_width <= 220:
                new_width = 530
            else:
                new_width = 530 + (new_width - 220) + 20

            window.geometry(f"{new_width}x300")

            return width, height
    except IOError:
        # 画像の読み込みに失敗した場合やサポートされていないフォーマットの場合
        messagebox.showerror("エラー", "マップ画像の読み込みに失敗しました")

# 初回起動時のUI変更
def initial_character_display(direction_frames):
    directions = ['down', 'left', 'right', 'up']
    for i, direction in enumerate(directions):
        canvas = tk.Canvas(window, width=64, height=64, bg='light gray')  # 灰色の四角形
        canvas.place(x=15 + (i * 70), y=135)
        if direction_frames != None:
            frame = direction_frames[direction][1]  # 2枚目のフレーム
            canvas.image_item = canvas.create_image(0, 0, anchor=tk.NW, image=frame)


def Get_CharacterImage_path():
    global restart_flg, character_image,direction_frames
    if not restart_flg:
        CharacterImage_path = Make_DiologPath()

        if CharacterImage_path == None:
            return #ダイアログ選択をキャンセルした場合
    
        textbox2.delete("1.0", tk.END)  # 既存のテキストを削除
        textbox2.insert(tk.END, CharacterImage_path)  # 文字列更新
    else:
        CharacterImage_path = textbox2.get(1.0,'end-1c') #Textbox2の内容を改行を含めずに取得

    button5.config(state=tk.NORMAL)
    #マップとキャラ何方も入力済みなら開始ボタンを起動
    check_text_fields3()

    try:
        global animation_running
        animation_running = True
        restart_flg = False
        button3["state"]="disabled"
        button4["state"]="normal"

        # CH画像を開く
        character_image = Image.open(CharacterImage_path)
        
        # 画像の幅を確認し、必要に応じてリサイズ
        original_width, original_height = character_image.size
        if original_width > 96:
            # 縦横比を保持しつつ幅を96ピクセルにリサイズ
            aspect_ratio = original_height / original_width
            new_height = int(96 * aspect_ratio)
            character_image = character_image.resize((96, new_height), Image.Resampling.LANCZOS)

        # CHシートのパス、フレームの幅と高さを指定
        frame_width = 32
        frame_height = 32

        directions = ['down', 'left', 'right', 'up']
        direction_frames = {}

        scale_factor = 2  # 拡大率

        for i, direction in enumerate(directions):
            # 各方向のフレームリストの作成
            frames = [character_image.crop((j * frame_width - 1, i * frame_height - 1, (j + 1) * frame_width, (i + 1) * frame_height)).resize(
                (frame_width * scale_factor, frame_height * scale_factor), Image.Resampling.LANCZOS) for j in range(3)]
            direction_frames[direction] = [ImageTk.PhotoImage(frame) for frame in frames]

        # 各方向のアニメーション表示のためのキャンバスを作成
        for i, direction in enumerate(directions):
            canvas = tk.Canvas(window, width=64, height=64, bg='light gray')
            canvas.place(x=15 + (i * 70), y=135)
            # アニメーションの初期設定
            current_frame_index = 0
            animation_sequence = [0, 1, 2, 1]
            # アニメーションの開始
            canvas.image_item = canvas.create_image(0, 0, anchor=tk.NW, image=direction_frames[direction][0])
            update_animation(canvas, direction_frames[direction], animation_sequence, current_frame_index)

    except IOError:
        messagebox.showerror("エラー", "CH画像の読み込みに失敗しました")

def update_animation(canvas, tk_frames, animation_sequence, current_frame_index):
    if not animation_running:
        return # アニメーションフラグがOFFに指定された際はアニメーションを止める
    
    # 現在のフレームの表示
    frame = tk_frames[animation_sequence[current_frame_index]]
    canvas.itemconfig(canvas.image_item, image=frame)

    # 次のフレームの設定
    current_frame_index = (current_frame_index + 1) % len(animation_sequence)

    # 300ミリ秒後に次のフレームに更新
    canvas.after(400, update_animation, canvas, tk_frames, animation_sequence, current_frame_index)

def start_animation():
    button3.config(state=tk.DISABLED)
    button4.config(state=tk.NORMAL)

    global animation_running,restart_flg
    animation_running = True
    restart_flg = True
    Get_CharacterImage_path()

def stop_animation():
    button3.config(state=tk.NORMAL)
    button4.config(state=tk.DISABLED)

    global animation_running,restart_flg
    animation_running = False
    restart_flg = False
    initial_character_display(direction_frames)

#======================================================================================================
def CH_Sheet_Split():

    Messagebox = tk.messagebox.askquestion('素材作成','キャラクターシートを分割して素材を作りますか？\n（元のシートには変更は加えません）')
    if Messagebox == 'no':
        return # いいえを選んだ場合は何もしない 

    frame_width=32
    frame_height=32
    columns, rows = 3, 4
    
    sprite_sheet_path = textbox2.get("1.0", "end-1c")
    File_Name = os.path.splitext(os.path.basename(sprite_sheet_path))[0]
    dir_name = os.path.dirname(os.path.abspath(argv[0]))

    output_folder = os.path.join(dir_name, File_Name) # 出力先パスを作成
    # フォルダが既に存在するかどうか確認
    if not os.path.isdir(output_folder):
        os.makedirs(output_folder) # フォルダが無かったら作成

    # 画像シートを分割して個別のPNG画像として保存
    sheet_image = Image.open(sprite_sheet_path)
    for row in range(rows):
        for col in range(columns):
            left = col * frame_width
            upper = row * frame_height
            right = left + frame_width
            lower = upper + frame_height
            frame = sheet_image.crop((left, upper, right, lower))
            
            # 保存ファイル名
            frame_count = row * columns + col + 1
            if frame_count < 4:
                frame_filename = f'{File_Name}_front_{frame_count}.png'
            elif frame_count < 7:
                frame_filename = f'{File_Name}_right_{frame_count - 3}.png'
            elif frame_count < 10:
                frame_filename = f'{File_Name}_left_{frame_count - 6}.png'
            else:
                frame_filename = f'{File_Name}_buck_{frame_count - 9}.png'

            # 現在のディレクトリに保存            
            frame.save(output_folder + '\\' + frame_filename)

    messagebox.showinfo("分割完了", "シートの素材化が完了しました")


#======================================================================================================
def on_click(event):
    # クリックした場所のxとy座標を取得
    x = event.x
    y = event.y
    
    # ステータスバーに表示
    status_bar_var.set(f'X: {x}, Y: {y}')

#======================================================================================================
def check_text_fields1():
    button6.config(state=tk.DISABLED)
def check_text_fields2():
    stop_animation()
    button3.config(state=tk.DISABLED)
    button4.config(state=tk.DISABLED)
    button5.config(state=tk.DISABLED)
    button6.config(state=tk.DISABLED)
def check_text_fields3():
    if textbox1.get("1.0", tk.END).strip() and textbox2.get("1.0", tk.END).strip():
        button6.config(state=tk.NORMAL)
    else:
        button6.config(state=tk.DISABLED)
#======================================================================================================
def get_screen_resolution():
    # フルスクリーンのサイズを取得
    user32 = ctypes.windll.user32
    width = user32.GetSystemMetrics(0)
    height = user32.GetSystemMetrics(1) - 70
    return width, height
#======================================================================================================
# UIを作成
# https://flytech.work/blog/16310/

window = tk.Tk()
window.title("Museum of Memories -Entrance-")

window_width = 530
window_height= 300
window.geometry(f"{window_width}x{window_height}")

Label_color ='Skyblue4'
Font_color = 'White'
font_settings = ("Segoe UI Black", 9, "bold")

# 背景色を設定
window.configure(bg=Label_color)

iconfile = os.path.join(os.path.dirname(__file__),'exe_logo.ico')
window.iconbitmap(default=iconfile)
#----------------------------------------------

# テキストボックスの作成
label2 = tk.Label(text='入りたい画像を選択してください', bg=Label_color,foreground=Font_color ,font=font_settings)
label2.place(x= 15, y=45)

textbox1 = tk.Text(window, wrap=tk.WORD,height=1, width=35,font=font_settings)
textbox1.place(x= 15, y=65)

button1 = tk.Button(window, text="選択", command=Get_MapImage_path)
button1.place(x= 260, y=60)

label2 = tk.Label(text='キャラクターシートを選んでください', bg=Label_color,foreground=Font_color ,font=font_settings)
label2.place(x= 15, y=85)

textbox2 = tk.Text(window, wrap=tk.WORD, height=1, width=35,font=font_settings)
textbox2.place(x= 15, y=105)

button2 = tk.Button(window, text="選択", command=Get_CharacterImage_path)
button2.place(x= 260, y=100)

label3 = tk.Label(window) 
canvas = tk.Canvas(window, width=200, height=160, bg='light gray')  # 灰色の四角形
canvas.place(x=310, y=40)

# プルダウンメニューの値
options = ["フルスクリーン", "スマホ画面" , "はがき・ポスカ", "1020x690" , "704x544"]
# 選択された値を格納する変数
selected_value = tk.StringVar()
# プルダウンメニューの作成
combo1 = ttk.Combobox(window, values=options,state="readonly",width=14)
combo1.set("704x544")
combo1.place(x=405, y=210)

label4 = tk.Label(text='Window Sise：', bg=Label_color,foreground=Font_color ,font=font_settings)
label4.place(x= 305, y=210)

label5 = tk.Label(text='横幅：0', bg=Label_color,foreground=Font_color,font=font_settings)
label5.place(x= 310, y=15)

label6 = tk.Label(text='縦幅：0', bg=Label_color,foreground=Font_color,font=font_settings)
label6.place(x= 400, y=15)

button3 = tk.Button(window, text=" ▶ ", command=start_animation, bg='#5B86FF', fg='white',state="disabled")
button3.place(x=90, y=215)

button4 = tk.Button(window, text=" ■ ", command=stop_animation, bg='#FF6362', fg='white',state="disabled")
button4.place(x=140, y=215)

button5 = tk.Button(window, text=" ✂ ", command=CH_Sheet_Split, bg='#66cdaa', fg='white' ,state="disabled")
button5.place(x=190, y=215)

direction_frames = None
initial_character_display(direction_frames)

Open_Image_path = os.path.join(os.path.dirname(__file__),'image','admission_img.png')
Open_Image = PhotoImage(file=Open_Image_path)

button6 = tk.Button(window, image=Open_Image ,command=Pygame_thread,state="disabled" ,width=250)
button6.place(x=25, y=250)

Title_Image_path = os.path.join(os.path.dirname(__file__),'image','Logo_image.png')
title_image = PhotoImage(file=Title_Image_path)

label1 = tk.Label(image = title_image,bg=Label_color)
label1.place(x= 25, y=3)

subart_Image_path = os.path.join(os.path.dirname(__file__),'image','art_image.png')
subart_image = PhotoImage(file=subart_Image_path)

label7 = tk.Label(image = subart_image, bg=Label_color)
label7.place(x= 310, y=235)

label8 = tk.Label(foreground=Label_color,text="0",bg=Label_color)
label8.place(x= 500, y=15)

#----------------------------------------------
# ステータスバー用の変数を作成
status_bar_var = tk.StringVar()
status_bar_var.set("")
# ステータスバーを作成
status_bar = tk.Label(window, textvariable=status_bar_var, fg="black", bd=1, relief=tk.SUNKEN, anchor=tk.W)
status_bar.pack(side=tk.BOTTOM, fill=tk.X)

#----------------------------------------------
#画面上でのイベント設定
window.bind('<Button-1>', on_click)
textbox1.bind("<KeyRelease>", lambda event: check_text_fields1())
textbox2.bind("<KeyRelease>", lambda event: check_text_fields2())

window.mainloop()


