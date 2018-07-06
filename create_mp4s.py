import sys
from subprocess import call
from glob import glob

def pngs_to_mp4(folder, bg, size='800x800'):
    print('making', folder)
    for f in glob(folder + '*.png'):
        args = ['convert', f,  '-fill', bg, '-opaque', 'none', '-resize', size, f.replace('.png', '.jpg')]
        # print(' '.join(args))
        call(args)

    outname = glob(folder + '*.png')[-1]
    outname = '_'.join(outname.split('_')[:-1]) + '.mp4'
    call(['ffmpeg', '-y', '-f', 'image2', '-pattern_type', 'glob', '-i', folder + '*.jpg',  '-vcodec', 'libx264', '-pix_fmt', 'yuv420p',  '-vf', 'scale=trunc(iw/2)*2:trunc(ih/2)*2', outname])


if __name__ == '__main__':
    #pngs_to_mp4(sys.argv[1], 'white')
    for foldername in glob("/Users/sam/Google Drive/Recordings/*"):
        foldername += '/'
        try:
            pngs_to_mp4(foldername, 'white', size='400x400')
        except Exception as e:
            print(e)
            continue


