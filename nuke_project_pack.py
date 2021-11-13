
#_*_coding:utf-8_*_

from PySide2 import QtWidgets
import nuke
import os
import shutil
import sys
import threading


file_nodes = ["Read","Camera2","ReadGeo2"]



class UI(QtWidgets.QWidget):
    # UI 界面
    def __init__(self):
        super(UI,self).__init__(None)
        self.setWindowTitle("nuke project pack")
        self.setFixedWidth(700)

        self.layout1 = QtWidgets.QHBoxLayout()
        self.label1 = QtWidgets.QLabel("pack to path:")
        self.pack_to_path = QtWidgets.QLineEdit()
        self.get_path_button = QtWidgets.QPushButton("选择打包到的路径")
        self.get_path_button.clicked.connect(self.open_file)
        self.layout1.addWidget(self.label1)
        self.layout1.addWidget(self.pack_to_path)
        self.layout1.addWidget(self.get_path_button)

        self.run_button = QtWidgets.QPushButton("开始打包")

        self.schedule_message = QtWidgets.QLabel("")

        self.all_layout = QtWidgets.QVBoxLayout()
        self.all_layout.addLayout(self.layout1)
        self.all_layout.addWidget(self.run_button)
        self.all_layout.addWidget(self.schedule_message)

        self.setLayout(self.all_layout)

    def open_file(self):
        # 打开文件选择器，然后把路径设置给 self.pack_to_path
        path = QtWidgets.QFileDialog.getExistingDirectory(self, "Open flie")
        self.pack_to_path.setText(path)

    def return_path(self):
        # 返回选择的路径
        path = self.pack_to_path.text()
        return path

    def set_schedule_message(self,message):
        # 更新进度显示
        self.schedule_message.setText(message)




class Copy_file():
    # 对传入的路径进行解析，然后进行复制
    def __init__(self,file,node_name,dst):
        self.file = file
        self.node_name = node_name
        self.dst = dst

        # 要拷贝的文件列表
        self.file_list = []


    def copy(self):
        # 复制文件
        dst_dir = os.path.join(self.dst,"material",self.node_name)
        if not os.path.exists(dst_dir):
            os.makedirs(dst_dir)

        for old_file_name in self.file_list:
            _,name = os.path.split(old_file_name)
            new_file_name = os.path.join(dst_dir,name)
            shutil.copyfile(old_file_name,new_file_name)


    def analyze_file(self):
        # 解析 file 是文件还是序列，然后添加到 self.copy_file_list

        if os.path.isfile(self.file):
            self.file_list.append(self.file)
            return

        # 对文件路径，不含帧号的文件名字，文件后缀进行分割
        file_dir_name,file_name = os.path.split(self.file)
        file_name,file_suffix = os.path.splitext(file_name)
        file_name,_ = os.path.splitext(file_name)

        # 遍历目录下的所有文件，忽略帧号比对文件名和后缀是否正确，正确的文件路径放到 self.copy_file_list
        for name in os.listdir(file_dir_name):
            if name.startswith(file_name) and name.endswith(file_suffix):
                self.file_list.append(os.path.join(file_dir_name,name))




class Nuke_project_pack():

    def __init__(self,ui):
        self.file_and_node_name = {}
        self.dst_dir = ""

        self.widget = ui
        self.widget.run_button.clicked.connect(self.run_pack)

    def pack(self):
        # 实际干活的
        self.widget.set_schedule_message("正在查找需要打包的节点")

        for node in nuke.allNodes():
            if node.Class() in file_nodes:
                file = node["file"].value()
                node_name = node["name"].value()
                self.file_and_node_name[file] = node_name

        count = len(self.file_and_node_name)
        index = 0
        self.widget.set_schedule_message("共找到 {} 个需要复制的文件".format(count))

        for file in self.file_and_node_name.keys():
            index += 1
            self.widget.set_schedule_message("正在复制文件，当前第{}个，共计{}个".format(index,count))
            node_name = self.file_and_node_name[file]
            copy_file = Copy_file(file=file,node_name=node_name,dst=self.dst_dir)
            copy_file.analyze_file()
            copy_file.copy()

        self.widget.set_schedule_message("正在保存工程")

        nk_path = nuke.Root().name()
        _,nk_name = os.path.split(nk_path)
        new_nk_name = os.path.join(self.dst_dir,nk_name)
        nuke.scriptSaveAs(new_nk_name)
        nuke.Root()["project_directory"].setValue("[file dirname [value root.name]]")

        self.widget.set_schedule_message("正在修改file参数")

        for node in nuke.allNodes():
            if node.Class() in file_nodes:
                file = node["file"].value()
                node_name = self.file_and_node_name[file]
                _,file_name = os.path.split(file)
                # new_file = os.path.join("[value root.project_directory]","material",node_name,file_name)
                new_file = "/".join(["[value root.project_directory]","material",node_name,file_name])
                node["file"].setValue(new_file)

        nuke.scriptSave()

        self.widget.set_schedule_message("打包完成")


    def run_pack(self):
        # 获取打包路径，开新线程运行
        self.dst_dir = self.widget.pack_to_path.text()
        if self.dst_dir == "":
            nuke.message("你需要设置打包的路径")
            return

        t = threading.Thread(target=self.pack)
        t.start()

