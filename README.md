![image](https://github.com/thxlxn/SprocketForge/blob/main/assets/fv4030as.png)
# SprocketForge
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)
![Issues](https://img.shields.io/github/issues/thxlxn/SprocketForge) 
[![Python Quality Check](https://github.com/thxlxn/SprocketForge/actions/workflows/python-lint.yml/badge.svg)](https://github.com/thxlxn/SprocketForge/actions/workflows/python-lint.yml) <br>
The universal tool for headache-less file editing in the popular video game Sprocket by Hamish Dunn.

> This whole thing is obviously still in progress and I do not have any ETAs. I plan on rolling out random useful (or not) features whenever I have free time in-between uni stuff. Any feedback is highly appreciated as I am still learning >.< <br>

Plans include (but not limited to):
- Advanced track and suspension modifications
- Structure merging
- Crew member modifications
- Vehicle modules painter

## 📏 File Editor
Current options:
- Change the armor thickness of every single face. Allows you to set the thickness value below 5mm for tiny geometry.
- Make the tracks invisible

## 🖼️ 3D Visualizer
Tries to replicate the feature available in Sprocket's official Discord server but with the edition of a slider that lets you spin the output image.
Do keep in mind that loading a **really heavy** blueprint can lead to your machine running out-of-memory.
Be careful with this... <sub>or don't, that's up to you</sub>

## 📁 Blueprint Packager
The packager lets the user upload .blueprint files, automatically retrieves the paintjob and all used decals as long as they are local (Not from a web link) and packs them into a .zip file together with the blueprints.
This allows for easy sharing of your blueprints without having to remember the assets you have used.

## 📅 Custom Era Creator
This automatically creates all the files needed for a custom era by taking user inputs. Please make sure you select the right directory in steamapps/common. I plan to add tooltips to each of the settings in eras but for now you may refer to the guides in the official Sprocket Discord server.

## 🛠️ Building Yourself
In case you wish to compile the executable yourself - with different settings or simply because you do not trust mine - you'll have to use **PyInstaller**. Don't forget to run `pip install -e .` in the root and then pass `--copy-metadata sprocketforge` as an argument to the compiler. <br>
For example:<br>
<pre>
pip install -e .
pyinstaller --onefile --noconsole --copy-metadata sprocketforge main.py
</pre>

### Contact<br>
<sup>Discord: the_len</sup>
