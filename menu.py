#!/usr/bin/env python
#_*_coding:utf-8_*_

import nuke
from nuke_project_pack import Nuke_project_pack,UI

ui = UI()
pack = Nuke_project_pack(ui)
nuke.menu("Nuke").addMenu("工程文件打包").addCommand("打包工程",pack.widget.show)


