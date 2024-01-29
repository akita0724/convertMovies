import tkinter.messagebox
import tkinter.filedialog
import tkinter
from os import path, environ
import ffmpeg
from tqdm import tqdm
from shutil import which
from platform import system

# ffmpegがインストールされているか確認
if which("ffmpeg") == None:
    print("ffmpegがインストールされていない、もしくは環境変数に追加されていません。")
    dir = input("ffmpegのパスを入力してください。(空白で終了) ->  ")
    if dir == "":
        exit()
    if path.exists(dir) == False:
        exit("パスが存在しません。")
    if path.endswith("ffmpeg.exe"):
        environ["ffmpeg"] = dir
    else:
        exit("パスが正しくありません。")


# ファイル名の一覧
fileType = {
    0: ["MOVファイル", "*.mov", ".mp4", "mp4"],
    1: ["WAVファイル", "*.wav", ".mp3", "mp3"],
    2: ["映像ファイル", "*.mp4;*.mov", ".mpg", "mpg"],
    3: ["MP4ファイル", "*.mp4", ".mp3", "mp3"],
    4: ["MP4ファイル", "*.mp4", ".mov", "mov"],
    5: ["MP3ファイル", "*.mp3", ".wav", "wav"],
    6: ["映像ファイル", "*.mp4;*.mov", "", ""],
    7: ["映像ファイル", "*.mp4;*.mov", ".png", "png"],
    # 7: ["音声ファイル", "*.mp3;*.wav"]
}


def intInput(text: list[str] = [], range: list[int] = [0, 2]):
    """
    整数値を入力させる関数
    """
    print("")
    print("\n".join(text))

    while True:
        try:
            value = input("->  ")
            if value == "":
                return 0
            if range[0] <= int(value) <= range[1]:
                return int(value)
            else:
                raise ValueError

        except ValueError:
            print(f"{range[0]} ~ {range[1]}の整数値を入力してください。")

        except:
            print("整数値を入力してください。")


def convertFName(fname: str, mode: int):
    if mode == 6:
        return fname[:fname.rfind(".")] + "_out" + fname[fname.rfind("."):]
    return fname[:fname.rfind(".")] + "_out" + fileType[mode][2]


# モードの選択
mode = intInput(
    ["モードを選択してください。",
     "0 : .mov -> .mp4",
     "1 : .wav -> .mp3",
     "2 : .mov/.mp4 -> .mpg",
     "3 : .mp4 -> .mp3",
     "4 : .mp4 -> .mov",
     "5 : .mp3 -> .wav",
     "6 : リサイズ・fps変更(映像)",
     "7 : 動画切り出し(映像)"], [0, 6])

# 動画の各種変更を指定
videoFPS = videoHeight = videoWidth = timeToCut = 0
if mode in [0, 2, 4, 6]:
    videoHeight = intInput(["変換後の縦のサイズを入力(0または空白で変換なし) (px)"], [1, 10000])
    videoWidth = intInput(["変換後の横のサイズを入力(0または空白で変換なし) (px)"], [1, 5000])
    videoFPS = intInput(["変換後のFPSを入力(0または空白で変換なし)"], [1, 100])

if mode == 7:
    timeToCut = intInput(["切り出す時間を入力(秒)"], [1, 1000000])

# ファイル選択ダイアログの表示
root = tkinter.Tk()
root.withdraw()
iDir = path.abspath(path.expanduser("~/Desktop"))

# Mac用
if system() == "Darwin":
    if mode in [0, 1, 3, 4, 5]:
        fTyp = [(fileType[mode][0], fileType[mode][1])]
    else:
        fTyp = [("MP4", "*.mp4"), ("mov", "*.mov")]
# Windows用
elif system() == "Windows":
    fTyp = [(fileType[mode][0], fileType[mode][1])]
else:
    exit("このOSはサポートされていません。\nMacOSまたはWindowsを使用してください。")

# 処理対象のファイルを選択
fileToConvert = tkinter.filedialog.askopenfilenames(
    filetypes=fTyp, initialdir=iDir)

# ファイルが選択されていない場合
if len(fileToConvert) == 0:
    exit("ファイルが選択されていません。")

for file in tqdm(fileToConvert):

    # ファイルが存在しない場合
    if path.exists(file) == False:
        print(f"ファイル{path.basename(file)}は存在しません。")
        continue

    # 出力ファイルが既に存在する場合
    if path.exists(convertFName(file, mode)):
        overwrite = intInput(
            [f"ファイル{path.basename(convertFName(file, mode))}は既に存在します。上書きしますか？",
             "0 : はい", "1 : いいえ"],
            [0, 1])
        if overwrite == 1:
            continue

    # ファイルの情報を取得
    probe = ffmpeg.probe(file)

    # 一切変更がない場合は変換しない
    if mode not in [1, 3, 5] and videoFPS == videoHeight == videoWidth == 0:
        break

    # 映像ファイルの情報を取得
    for stream in probe['streams']:
        if stream['codec_type'] == 'video':
            videoWidth = videoWidth or stream['width']
            videoHeight = videoHeight or stream['height']
            videoFPS = videoFPS or stream['r_frame_rate']

    if mode in [0, 4]:
        (ffmpeg
         .input(file)
         .output(convertFName(file, mode),
                 s=f"{videoWidth}:{videoHeight}",
                 format=fileType[mode][3],
                 pix_fmt="yuv420p",)
         .run(overwrite_output=True, quiet=True))

    elif mode in [6]:
        (ffmpeg
         .input(file)
         .output(convertFName(file, mode),
                 s=f"{videoWidth}:{videoHeight}",)
         .run(overwrite_output=True, quit=True))

    elif mode in [1, 3, 5]:
        (ffmpeg
         .input(file)
         .output(convertFName(file, mode))
         .run(overwrite_output=True, quiet=True))

    elif mode in [2]:
        ffmpeg.input(file).output(convertFName(file, mode),
                                  c='mpeg2video',
                                  vf=f'scale={videoWidth}:{videoHeight},format=yuv420p,fps=30000/1001',
                                  vsync=1,
                                  target='ntsc-dvd',
                                  aspect='16:9').run(overwrite_output=True, quiet=True)

        ffmpeg.input(file).output(convertFName(file, mode),
                                  c='mpeg2video',
                                  vf=f'scale={videoWidth}:{videoHeight},fps=30000/1001',
                                  vsync=1,
                                  target='ntsc-dvd',
                                  aspect='16:9',
                                  b='6000k',
                                  maxrate='9000k').run(overwrite_output=True, quiet=True)
    elif mode in [7]:
        (ffmpeg
         .input(file)
         .output(convertFName(file, mode), ss=timeToCut, flames=1).
         run(
             overwrite_output=True, quiet=True))

print("変換が完了しました。")
