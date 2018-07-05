import sys
from subprocess import call
from glob import glob

def pngs_to_mp4(folder, bg):
    for f in glob(folder + '*.png'):
        call(['convert', f,  '-fill', bg, '-opaque', 'none', f.replace('.png', '.jpg')])

    outname = glob(folder + '*.png')[-1]
    outname = '_'.join(outname.split('_')[:-1]) + '.mp4'
    call(['ffmpeg', '-y', '-f', 'image2', '-pattern_type', 'glob', '-i', folder + '*.jpg',  '-vcodec', 'libx264', '-pix_fmt', 'yuv420p',  '-vf', 'scale=trunc(iw/2)*2:trunc(ih/2)*2', outname])


if __name__ == '__main__':
    pngs_to_mp4(sys.argv[1], 'white')


