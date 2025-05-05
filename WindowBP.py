from PyQt5.QtWidgets import (QApplication, QMainWindow, 
                             QGridLayout, QWidget,
                             QPushButton, QFileDialog,
                             QShortcut, QToolButton, QDialog,
                             QLineEdit) 
from PyQt5.QtGui import QIcon, QKeySequence, QPixmap
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel, QVBoxLayout
import os
import json
from pathlib import Path
from PyQt5.QtCore import QSize
import win32ui
import win32gui
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QSystemTrayIcon
import win32con
from PIL import Image
from PyQt5.QtWidgets import QProgressDialog

import sys
from PyQt5.QtWidgets import QMenu, QMessageBox
from PyQt5.QtGui import QCursor
from PyQt5.QtCore import QT_VERSION_STR 
from pynput import keyboard
print("PyQt5版本:", QT_VERSION_STR)  
print("系统平台:", sys.platform)

global_layout = None  
window_instance = None
listener = None
items = [[None for _ in range(9)] for _ in range(4)]
data_file = Path(os.getenv('APPDATA')) / 'DesktopBackpack' / 'BP.json'





tray_icon = None
def copy_textures_to_appdata():
    try:
       
        src_textures = os.path.join(os.path.dirname(__file__), "textures")
  
        dst_textures = os.path.join(os.getenv('APPDATA'), 'DesktopBackpack', 'textures')
      
        os.makedirs(dst_textures, exist_ok=True)
        
   
        if os.path.exists(dst_textures) and len(os.listdir(dst_textures)) > 0:
            print("目标textures文件夹不为空，跳过复制")
            return
            
 
        if os.path.exists(src_textures):
            import shutil
            
       
            progress_dialog = QProgressDialog("正在复制文件到存储并完成文件初始化...", "取消", 0, 100, window_instance)
            progress_dialog.setWindowTitle("初始化")
            progress_dialog.setWindowModality(Qt.WindowModal)
            progress_dialog.setAutoClose(True)
            progress_dialog.show()
            
   
            all_files = []
            for root, dirs, files in os.walk(src_textures):
                for file in files:
                    all_files.append(os.path.join(root, file))
            
            total_files = len(all_files)
            progress_dialog.setMaximum(total_files)
            
           
            for i, src_path in enumerate(all_files, 1):
                if progress_dialog.wasCanceled():
                    break
                    
                rel_path = os.path.relpath(src_path, src_textures)
                dst_path = os.path.join(dst_textures, rel_path)
                
        
                os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                shutil.copy2(src_path, dst_path)
                
                progress_dialog.setValue(i)
                QApplication.processEvents() 
            
            progress_dialog.close()
            print(f"已复制textures文件夹到: {dst_textures}")
        else:
            print("警告: 源textures文件夹不存在")
    except Exception as e:
        print(f"复制textures文件夹失败: {e}")


def toggle_window(window):
    if window.isVisible():
        window.hide()
    else:
        window.show()
        window.raise_()
        window.activateWindow()

def setup_hotkeys(window):
    global key_states
    key_states = {
        'alt': False,  
        'e': False,
        'space': False
    }

    def on_press(key):
        try:
           
            if key == keyboard.Key.alt or key == keyboard.Key.alt_l or key == keyboard.Key.alt_r:
                key_states['alt'] = True
            elif hasattr(key, 'char') and key.char == 'e':
                key_states['e'] = True
            elif key == keyboard.Key.space:
                key_states['space'] = True
                if window_instance and window_instance.isVisible():
                    add_item_to_selected_cell()
            
          
            if key_states['alt'] and key_states['e']:
                toggle_window(window)
               
                key_states['alt'] = False
                key_states['e'] = False
                
        except Exception as e:
            print(f"按键检测错误: {e}")

    def on_release(key):
        try:
         
            if key == keyboard.Key.alt or key == keyboard.Key.alt_l or key == keyboard.Key.alt_r:
                key_states['alt'] = False
            elif hasattr(key, 'char') and key.char == 'e':
                key_states['e'] = False
            elif key == keyboard.Key.space:
                key_states['space'] = False
        except:
            pass
    
    global listener
    listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    listener.start()
    QShortcut(QKeySequence(Qt.Key_Escape), window).activated.connect(window.hide)

def add_item_to_selected_cell():
 
    focused_widget = QApplication.focusWidget()
    if not isinstance(focused_widget, QToolButton):
        return

    index = global_layout.indexOf(focused_widget)
    if index == -1:
        return
        
    row, col, _, _ = global_layout.getItemPosition(index)
    show_file_chooser(row, col)

def center_window(window):
    frame = window.frameGeometry()
    center_point = QApplication.desktop().availableGeometry().center()
    frame.moveCenter(center_point)
    window.move(frame.topLeft())
def show_context_menu(row, col):
    print(f"\n=== 右键菜单调试 ===")
    print(f"位置: {row},{col}")
    print(f"单元格内容: {items[row][col]}")
    print(f"窗口实例: {'有效' if window_instance else '无效'}")
    print(f"全局布局: {'有效' if global_layout else '无效'}")
    
    btn = global_layout.itemAtPosition(row, col).widget()
    print(f"按钮对象: {'存在' if btn else '不存在'}")
    
    if not btn or not items[row][col]:
        print("条件不满足，不显示菜单")
        return
    if not items[row][col]:
        print("单元格为空，不显示菜单")
        return
        
    if not items[row][col]:
        return
        
    menu = QMenu(window_instance)  
    delete_action = menu.addAction("删除")
    

    btn = global_layout.itemAtPosition(row, col).widget()
    if btn is None: 
        return
    global_pos = btn.mapToGlobal(btn.rect().center()) 
    
    
    action = menu.exec_(global_pos)
    
    if action == delete_action:
        
        reply = QMessageBox.question(window_instance, '确认删除',  
                                    '确定要删除这个文件吗？',
                                    QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            items[row][col] = None
            save_items()
            update_grid(global_layout)
def delete_item(row, col):

    reply = QMessageBox.question(window_instance, '确认删除',
                               '确定要删除这个文件吗？',
                               QMessageBox.Yes | QMessageBox.No)
    if reply == QMessageBox.Yes:
        items[row][col] = None
        save_items()
        update_grid(global_layout)
def on_cell_double_click(event, row, col):
    if event.button() == Qt.LeftButton:
        if items[row][col]:
            try:
                os.startfile(items[row][col])
            except Exception as e:
                print(f"无法打开文件: {e}")
    event.accept()
def create_backpack_grid(parent):
    grid = QWidget(parent)
    layout = QGridLayout(grid)
    

    parent_width = parent.width()
    
    layout.setVerticalSpacing(15)

    layout.setHorizontalSpacing(3)
    layout.setContentsMargins(0, 16, 0, 0)  
    grid.setStyleSheet("background: transparent; border: none;")
    layout.setRowMinimumHeight(3, 90)

    for row in range(4):
        for col in range(9):
            btn = QToolButton() 
            btn.setFixedSize(64, 64)
            btn.setFocusPolicy(Qt.StrongFocus)
            btn.clicked.disconnect() if btn.receivers(btn.clicked) > 0 else None
            btn.setStyleSheet("QToolButton::menu-indicator { image: none; }")
         
            btn.mouseDoubleClickEvent = lambda event, r=row, c=col: on_cell_double_click(event, r, c)
            
            menu = QMenu()
            delete_action = menu.addAction("删除")
            delete_action.triggered.connect(lambda _, r=row, c=col: delete_item(r, c))
            btn.setMenu(menu)
            btn.clicked.connect(lambda _, r=row, c=col: on_cell_click(r, c))
         
            btn.customContextMenuRequested.connect(
                lambda pos, r=row, c=col: show_context_menu(r, c)
            )
            if items[row][col]:
                item_data = items[row][col]
                if isinstance(item_data, dict):
                    file_path = item_data["path"]
                    file_name = os.path.basename(file_path)
                else:
                    file_path = item_data
                    file_name = os.path.basename(item_data)
                
                icon_path = get_file_icon(item_data)
                if icon_path:

                    pixmap = QPixmap(icon_path)
                    if not pixmap.isNull():
                        btn.setIcon(QIcon(pixmap))
                        btn.setIconSize(QSize(16,16))  
                    print(f"成功获取图标: {icon_path}")
                    btn.setIcon(QIcon(icon_path))
                    btn.setIconSize(QSize(30,30))
                    btn.setToolTip(f"文件名: {file_name}\n路径: {file_path}")
                else:
                    print(f"获取图标失败，但仍保留文件: {file_path}")
                    btn.setText(file_name[:5])
                    btn.setToolTip(f"文件名: {file_name}\n路径: {file_path}")
            else:
                btn.setText('+')
            
            btn.clicked.connect(lambda _, r=row, c=col: on_cell_click(r, c))
            layout.addWidget(btn, row, col)
    
    return grid, layout
def update_grid(layout):
    for i in reversed(range(layout.count())):
        layout.itemAt(i).widget().setParent(None)
        
    for row in range(4):
        for col in range(9):
            btn = QToolButton()
            btn.setFixedSize(64, 64)
            btn.setFocusPolicy(Qt.StrongFocus)
            btn.mouseDoubleClickEvent = lambda event, r=row, c=col: on_cell_double_click(event, r, c)
            btn.setStyleSheet("QToolButton::menu-indicator { image: none; }")
            
            btn.setContextMenuPolicy(Qt.CustomContextMenu)
            btn.customContextMenuRequested.connect(
                lambda pos, r=row, c=col: show_context_menu(r, c)
            )
            menu = QMenu()
            delete_action = menu.addAction("删除")
            delete_action.triggered.connect(lambda _, r=row, c=col: delete_item(r, c))
            btn.setMenu(menu)
            if items[row][col]:
                item_data = items[row][col]
                if isinstance(item_data, dict):  
                    file_path = item_data["path"]
                    file_name = os.path.basename(file_path)
                    metadata = item_data.get("metadata", {})
                    
                    
                    tooltip = """
                    <div style="color: #ffffff; font-size: 17px;">
                        <b>{}</b> <br>
                        <b></b> {}<br>
                        {}
                        
                    
                        {}<br>
                        <i style="color: #55aaff; font-style: italic;">Minecraft</i><br>
                    </div>
                    """.format(
                        metadata.get('name', file_name),
                        file_path,
                        f'<span style="color: #a0a0a0;">{metadata["desc"]}</span><br>' if metadata.get('desc') else "",
                        f"minecraft:{', '.join(metadata['tags'])}" if metadata.get('tags') else ""
                    )
                else:  # 旧格式
                    file_path = item_data
                    file_name = os.path.basename(item_data)
                    tooltip = f"""
                    <div style="color: #ffffff; font-size: 15px;">
                        <b>文件名:</b> {file_name}<br>
                        <b>路径:</b> {file_path}
                    </div>
                    """
                icon_path = get_file_icon(item_data)
                if icon_path:
                    btn.setIcon(QIcon(icon_path))
                    btn.setIconSize(QSize(52,52))
                    btn.setToolTip(tooltip)  # 使用新的tooltip
                else:
                    btn.setText(file_name[:5])
                    btn.setToolTip(tooltip)  # 使用新的tooltip
            else:
                btn.setText('')
            
            btn.clicked.connect(lambda _, r=row, c=col: on_cell_click(r, c))
            layout.addWidget(btn, row, col)

def on_cell_click(row, col):
    if items[row][col]:
        try:
         
            file_path = items[row][col]["path"] if isinstance(items[row][col], dict) else items[row][col]
            os.startfile(file_path)  # 打开文件
        except Exception as e:
            print(f"无法打开文件: {e}")
    else:  # 如果格子是空的
        show_file_chooser(row, col)  # 显示文件选择对话框

def show_icon_chooser(row, col, file_path, metadata=None):
    # 创建图标选择对话框
    icon_dialog = QDialog(window_instance)
    icon_dialog.setWindowTitle("选择图标")
    icon_dialog.setWindowModality(Qt.ApplicationModal)
    layout = QVBoxLayout()

    # 默认图标选项
    default_btn = QPushButton("使用默认图标")
    default_btn.clicked.connect(lambda: [
        set_item_with_icon(row, col, file_path, "default", None, metadata),
        icon_dialog.close()
    ])


    recommend_btn = QPushButton("使用推荐图标")
    file_ext = os.path.splitext(file_path)[1][1:].lower()
    recommend_btn.clicked.connect(lambda: [
        set_item_with_icon(row, col, file_path, "recommended", file_ext, metadata),
        icon_dialog.close()
    ])

    custom_btn = QPushButton("选择自定义图标")
    custom_btn.clicked.connect(lambda: [
        choose_custom_icon(row, col, file_path, metadata),
        icon_dialog.close()
    ])


    layout.addWidget(default_btn)
    layout.addWidget(recommend_btn)
    layout.addWidget(custom_btn)
    
    icon_dialog.setLayout(layout)
    icon_dialog.exec_()


def show_file_chooser(row, col):
    file_path, _ = QFileDialog.getOpenFileName(None, "选择文件")
    if file_path:
    
        icon_dialog = QDialog(window_instance)
        icon_dialog.setWindowTitle("选择图标")
        icon_dialog.setWindowModality(Qt.ApplicationModal)
        layout = QVBoxLayout()
        
    
        default_btn = QPushButton("使用默认图标")
        default_btn.clicked.connect(lambda: [
            set_item_with_icon(row, col, file_path, "default"),
            icon_dialog.close()
        ])
        
   
        recommend_btn = QPushButton("使用推荐图标")
        file_ext = os.path.splitext(file_path)[1][1:].lower()
        recommend_btn.clicked.connect(lambda: [
            set_item_with_icon(row, col, file_path, "recommended", file_ext),
            icon_dialog.close()
        ])
        

        custom_btn = QPushButton("选择自定义图标")
        custom_btn.clicked.connect(lambda: [
            choose_custom_icon(row, col, file_path),
            icon_dialog.close()
        ])
        meta_dialog = QDialog(window_instance)
        meta_dialog.setWindowTitle("文件信息")
        meta_layout = QVBoxLayout()
  
        name_label = QLabel("名称:")
        name_edit = QLineEdit(os.path.basename(file_path))
        
        desc_label = QLabel("描述:")
        desc_edit = QLineEdit()
        
        tags_label = QLabel("标签(逗号分隔):")
        tags_edit = QLineEdit()
        
        # 添加确认按钮
        confirm_btn = QPushButton("确认")
        def on_confirm():
            meta_dialog.close()
            show_icon_chooser(row, col, file_path, {
                'name': name_edit.text(),
                'desc': desc_edit.text(),
                'tags': [tag.strip() for tag in tags_edit.text().split(',') if tag.strip()]
            })
            
        confirm_btn.clicked.connect(on_confirm)
        
        # 添加到布局
        meta_layout.addWidget(name_label)
        meta_layout.addWidget(name_edit)
        meta_layout.addWidget(desc_label)
        meta_layout.addWidget(desc_edit)
        meta_layout.addWidget(tags_label)
        meta_layout.addWidget(tags_edit)
        meta_layout.addWidget(confirm_btn)
        
        meta_dialog.setLayout(meta_layout)
        meta_dialog.exec_()


def set_item_with_icon(row, col, file_path, icon_type, file_ext=None, metadata=None):
    import Icons
    icon_config = Icons.icon_config
    appdata_textures = os.path.join(os.getenv('APPDATA'), 'DesktopBackpack', 'textures')
    
    if icon_type == "default":
        icon_path = os.path.normpath(os.path.join(appdata_textures, "item", "default.png"))
    elif icon_type == "recommended":
        file_ext = file_ext.strip().lower() if file_ext else ""
        if file_ext in icon_config["recommended"]:
            # 获取原始推荐路径
            recommended_path = icon_config["recommended"][file_ext]
            # 提取目录名和文件名
            dir_name = os.path.dirname(recommended_path).split('/')[-1]  # 获取block或item
            icon_name = os.path.basename(recommended_path)
            # 使用正确的目录路径
            icon_path = os.path.normpath(os.path.join(appdata_textures, dir_name, icon_name))
        else:
            icon_path = os.path.normpath(os.path.join(appdata_textures, "item", "default.png"))
    elif icon_type == "custom":
        try:
            import shutil
            custom_icon_dir = os.path.join(appdata_textures, "custom")
            os.makedirs(custom_icon_dir, exist_ok=True)
            dst_path = os.path.join(custom_icon_dir, os.path.basename(file_ext))
            shutil.copy2(file_ext, dst_path)
            icon_path = dst_path
        except Exception as e:
            print(f"复制自定义图标到AppData失败: {e}")
            icon_path = os.path.abspath(file_ext)
    
    items[row][col] = {
        "path": os.path.abspath(file_path),
        "icon": icon_path,
        "icon_type": icon_type,
        "metadata": metadata or {
            'name': os.path.basename(file_path),
            'desc': '',
            'tags': []
        }
    }
    save_items()
    update_grid(global_layout)

def choose_custom_icon(row, col, file_path, metadata=None):
    appdata_custom = os.path.join(os.getenv('APPDATA'), 'DesktopBackpack', 'textures', 'custom')
    os.makedirs(appdata_custom, exist_ok=True)
    
    icon_path, _ = QFileDialog.getOpenFileName(
        None, "选择自定义图标", 
        appdata_custom,
        "Images (*.png *.jpg *.jpeg *.bmp)"
    )
    if icon_path:
        set_item_with_icon(row, col, file_path, "custom", icon_path, metadata)

def get_file_icon(file_data, size=(64,64)):
    # 处理新旧数据结构
    if isinstance(file_data, dict):  # 如果是字典格式数据
        file_path = file_data["path"]
        icon_path = file_data["icon"]  # 修正这里，之前错误地使用了file_path["icon"]
    else:  # 如果是旧格式的纯路径字符串
        file_path = file_data
        icon_path = None
    
    # 如果已有指定图标路径，优先使用
    if icon_path and os.path.exists(icon_path):
        try:
            temp_path = os.path.join(os.getenv('TEMP'), f"temp_icon_{os.getpid()}.png")
            img = Image.open(icon_path)
            # 使用高质量缩放算法
            img = img.resize(size, Image.Resampling.NEAREST)  # 使用最近邻插值保持锐利边缘
            img.save(temp_path, quality=100)
            return temp_path
        except Exception as e:
            print(f"加载指定图标失败: {e}")
    try:
        if not os.path.exists(file_path):
            print(f"文件不存在: {file_path}")
            return None
            
        file_path = os.path.abspath(file_path)
        
        # 尝试直接加载图片文件
        if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.ico')):
            try:
                temp_path = os.path.join(os.getenv('TEMP'), f"temp_icon_{os.getpid()}.png")
                img = Image.open(file_path)
                img = img.resize(size, Image.Resampling.LANCZOS)
                img.save(temp_path)
                return temp_path
            except Exception as img_error:
                print(f"直接加载图片失败: {img_error}")

        # 使用ctypes实现图标获取
        try:
            import ctypes
            from ctypes import wintypes
            
            # 定义结构体
            class SHFILEINFOW(ctypes.Structure):
                _fields_ = [
                    ("hIcon", ctypes.c_void_p),
                    ("iIcon", ctypes.c_int),
                    ("dwAttributes", ctypes.c_ulong),
                    ("szDisplayName", ctypes.c_wchar * 260),
                    ("szTypeName", ctypes.c_wchar * 80)
                ]
            
            # 定义API参数
            shell32 = ctypes.windll.shell32
            SHGFI_ICON = 0x100
            SHGFI_LARGEICON = 0x0
            SHGFI_SYSICONINDEX = 0x4000
            
            # 调用Windows API
            shfi = SHFILEINFOW()
            file_attr = win32con.FILE_ATTRIBUTE_NORMAL
            if os.path.isdir(file_path):
                file_attr = win32con.FILE_ATTRIBUTE_DIRECTORY
            
            # 获取图标句柄
            ret = shell32.SHGetFileInfoW(
                file_path,
                file_attr,
                ctypes.byref(shfi),
                ctypes.sizeof(shfi),
                SHGFI_ICON | SHGFI_LARGEICON | SHGFI_SYSICONINDEX
            )
            
            if not ret or not shfi.hIcon:
                print("无法获取图标句柄")
                return None
            
            # 创建兼容位图
            hdc = win32ui.CreateDCFromHandle(win32gui.GetDC(0))
            hbmp = win32ui.CreateBitmap()
            hbmp.CreateCompatibleBitmap(hdc, *size)
            hdc = hdc.CreateCompatibleDC()
            hdc.SelectObject(hbmp)
            
            # 绘制图标（保留透明度）
            win32gui.DrawIconEx(
                hdc.GetHandleOutput(),
                0, 0,
                shfi.hIcon,
                size[0], size[1],
                0, None, 0x0003  # DI_NORMAL | DI_COMPAT
            )
            
            # 转换为PIL图像
            bmpinfo = hbmp.GetInfo()
            bmpstr = hbmp.GetBitmapBits(True)
            img = Image.frombuffer(
                'RGBA',
                (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
                bmpstr, 'raw', 'BGRA', 0, 1
            )
            
            temp_path = os.path.join(os.getenv('TEMP'), f"temp_icon_{os.getpid()}.png")
            img.save(temp_path)
            win32gui.DestroyIcon(shfi.hIcon)
            return temp_path
            
        except Exception as sys_error:
            print(f"系统图标获取失败: {sys_error}")
            return None
            
    except Exception as e:
        print(f"图标处理异常: {e}")
        import traceback
        traceback.print_exc()
        return None

def load_items():
    try:
        os.makedirs(data_file.parent, exist_ok=True)
        if data_file.exists():
            with open(data_file, 'r') as f:
                data = json.load(f)
                
                # 处理旧格式数据(纯路径字符串)和新格式数据(字典)的兼容
                if isinstance(data, list):  # 旧格式
                    items[:] = data
                else:  # 新格式
                    items[:] = data.get("items", [[None for _ in range(9)] for _ in range(4)])
                    # 只更新配置文件中存在的键，保留默认配置
                    saved_config = data.get("icon_config", {})
                    
    except Exception as e:
        print(f"加载背包数据失败: {e}")

def save_items():
    try:
        with open(data_file, 'w') as f:
            json.dump({
                "items": items,
                # 可以添加其他需要保存的配置信息
            }, f, indent=4)  # 使用indent让JSON更易读
    except Exception as e:
        print(f"保存背包数据失败: {e}")

def create_window():
    global window_instance, tray_icon
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    window = QMainWindow()  
    copy_textures_to_appdata()
    window_instance = window
    app.setStyleSheet("""
        QToolTip {
            font-family: "Minecraft";
            font-size: 15px;
            color: #ffffff;
            background-color: #333333;
            border: 1px solid #555555;
            padding: 5px;
            border-radius: 3px;
            opacity: 230;
        }
    """)
    # 调试信息 - 检查图标路径
    local_icon = os.path.join(os.path.dirname(__file__), "textures", "item", "default.png")
    appdata_icon = os.path.join(os.getenv('APPDATA'), 'DesktopBackpack', 'textures', 'item', 'nether_star.png')
    print(f"本地图标路径: {local_icon}, 存在: {os.path.exists(local_icon)}")
    print(f"AppData图标路径: {appdata_icon}, 存在: {os.path.exists(appdata_icon)}")

    if not QSystemTrayIcon.isSystemTrayAvailable():
        print("警告: 系统不支持托盘图标")
    else:
        # 创建临时图标作为后备
        temp_icon = QIcon()
        
        # 尝试加载图标文件
        icon_paths = [
            local_icon,
            appdata_icon,
            "./icons/nether_star.png"  # Qt资源路径
        ]
        
        for path in icon_paths:
            if os.path.exists(path) if not path.startswith(":") else True:
                try:
                    temp_icon = QIcon(path)
                    print(f"成功加载图标: {path}")
                    break
                except Exception as e:
                    print(f"加载图标失败 {path}: {e}")
        
        
        # 创建托盘图标
        tray_icon = QSystemTrayIcon(temp_icon, window)
        tray_icon.setToolTip("Desktop Backpack")
        
        # 创建托盘菜单
        tray_menu = QMenu()
        show_action = tray_menu.addAction("显示窗口")
        show_action.triggered.connect(window.show)
        
        hide_action = tray_menu.addAction("隐藏窗口")
        hide_action.triggered.connect(window.hide)
        
        quit_action = tray_menu.addAction("退出")
        quit_action.triggered.connect(QApplication.quit)
        
        tray_icon.setContextMenu(tray_menu)
        
        # 确保图标设置成功
        if not tray_icon.icon().isNull():
            tray_icon.show()
            print("托盘图标已成功显示")
        else:
            print("警告: 无法设置有效的托盘图标")


    window.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
    window.setFixedSize(730, 350)
    center_window(window)
    window_instance = window 
    # 主界面设置
    main_widget = QWidget()
    window.setCentralWidget(main_widget)
    
    # 背景设置
    bg_path = os.path.abspath("./textures/gui/container/inventory.png")
    background = QLabel(main_widget)
    background.setPixmap(QPixmap(bg_path).scaled(
        window.width(), window.height(),
        Qt.IgnoreAspectRatio,
        Qt.SmoothTransformation
    ))
    background.setGeometry(0, 0, window.width(), window.height())
    background.lower()
    
    # 创建网格
    grid, layout = create_backpack_grid(main_widget)
    main_layout = QVBoxLayout(main_widget)
    main_layout.setContentsMargins(0, 0, 0, 0)
    main_layout.addWidget(grid)
    
    # 将layout设为全局变量
    global global_layout
    global_layout = layout
    
    # 加载数据
    load_items()
    update_grid(layout)
    
    # 设置热键
    setup_hotkeys(window)
    
    return window

if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)
        window = create_window()
        window.show()
        sys.exit(app.exec_())
    except KeyboardInterrupt:
        print("\n程序已被用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"程序发生错误: {e}")
        sys.exit(1)
