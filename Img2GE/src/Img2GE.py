#!/usr/local/bin/python2.7
# encoding: utf-8
'''
Img2GE -- Plot local images w/ GPS data onto Google Earth VIA crafted .kml

Img2GE is a description

It defines classes_and_methods

@author:     user_name

@copyright:  2014 organization_name. All rights reserved.

@license:    license

@contact:    user_email
@deffield    updated: Updated
'''

import sys
import os

import exifread
import simplekml

from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter
from logging import getLogger, basicConfig
from itertools import groupby

basicConfig()
log = getLogger()


__all__ = []
__version__ = 0.1
__date__ = '2014-07-22'
__updated__ = '2014-07-22'

DEBUG = 0
TESTRUN = 0
PROFILE = 1

class CLIError(Exception):
    '''Generic exception to raise and log different fatal errors.'''
    def __init__(self, msg):
        super(CLIError).__init__(type(self))
        self.msg = "E: %s" % msg
    def __str__(self):
        return self.msg
    def __unicode__(self):
        return self.msg


def process_image(x):
    with open(x,'rb') as fd:
        tag = exifread.process_file(fd)
    tag['Filename'] = x
    return tag

def import_images(inpath, recurse=True):
    '''
    @return: list of exifs (dict v=k pairs)
    '''
    imgs = []
    for root, dirs, files in os.walk(inpath):  # @UnusedVariable
        newimgs = filter(lambda x:os.path.splitext(x)[1].lower() in ['.jpg','.jpeg'],files)
        imgs.extend(map(lambda x:os.path.join(root,x),newimgs))
        if not recurse:
            break
    
    exifs = map(lambda x:process_image(x), imgs)
    log.info("Found %s images."%len(exifs))
    return exifs

def get_coords(exif):
    lng = exif['GPS GPSLongitude'].values
    lng = lng[0].decimal() + lng[1].decimal()/60 + lng[2].decimal()/3600
    if str(exif['GPS GPSLongitudeRef']) == 'W':
        lng *= -1
    lat = exif['GPS GPSLatitude'].values
    lat = lat[0].decimal() + lat[1].decimal()/60 + lat[2].decimal()/3600
    if str(exif['GPS GPSLatitudeRef']) == 'S':
        lat *= -1
    return (lng,lat)
    
def create_kml(exifs,filename="Img2GE.kml"):
    kml = simplekml.Kml()
    for grp_name, exifs in groupby(exifs,key=lambda x:os.path.dirname(x['Filename'])):
        folder_created = False
        for exif in exifs:
            log.debug(str(exif))
            if 'GPS GPSLatitude' in exif and 'GPS GPSLongitude' in exif:
                #Only create folders if there are images with EXIF data
                if folder_created == False:
                    fldr = kml.newfolder(name=grp_name)
                    folder_created = True
                coords = get_coords(exif)
                photo = fldr.newphotooverlay(name=os.path.basename(exif['Filename']))
                hdg = exif.get('GPS GPSImgDirection',None)
                if hdg is None:
                    hdg = 0
                else:
                    hdg = hdg.values[0].decimal()
                photo.camera = simplekml.Camera(longitude=coords[0], latitude=coords[1], altitude=500, heading=hdg,
                                                altitudemode=simplekml.AltitudeMode.relativetoground)
                photo.icon.href = exif['Filename']
                photo.style.iconstyle.icon.href = exif['Filename']
                photo.viewvolume = simplekml.ViewVolume(-25,25,-15,15,1)
                photo.point.coords = [coords]
    log.info("KML saved as: %s"%filename)
    kml.save(filename)

def main(argv=None): # IGNORE:C0111
    '''Command line options.'''

    if argv is None:
        argv = sys.argv
    else:
        sys.argv.extend(argv)

    program_name = os.path.basename(sys.argv[0])
    program_version = "v%s" % __version__
    program_build_date = str(__updated__)
    program_version_message = '%%(prog)s %s (%s)' % (program_version, program_build_date)
    program_shortdesc = __import__('__main__').__doc__.split("\n")[1]
    program_license = '''%s

  Created by user_name on %s.
  Copyright 2014 organization_name. All rights reserved.

  Licensed under the Apache License 2.0
  http://www.apache.org/licenses/LICENSE-2.0

  Distributed on an "AS IS" basis without warranties
  or conditions of any kind, either express or implied.

USAGE
''' % (program_shortdesc, str(__date__))

    try:
        # Setup argument parser
        parser = ArgumentParser(description=program_license, formatter_class=RawDescriptionHelpFormatter)
        parser.add_argument("-r", "--recursive", dest="recurse", action="store_true", help="recurse into subfolders [default: %(default)s]")
        parser.add_argument("-o", "--output", dest="output", default="Img2GE.kml", help="set output filename [default: %(default)s]")
        parser.add_argument("-v", "--verbose", dest="verbose", action="count", help="set verbosity level (-vv for most verbose) [default: %(default)s]")
        parser.add_argument('-V', '--version', action='version', version=program_version_message)
        parser.add_argument(dest="paths", help="paths to folder(s) with image(s) [default: %(default)s]", metavar="path", nargs='+')

        # Process arguments
        args = parser.parse_args()

        paths = args.paths
        verbose = args.verbose
        recurse = args.recurse
        outputfn = args.output

        if verbose > 0:
            if verbose > 2: verbose = 2
            print("Verbose mode: %s" % verbose)
            log.setLevel(30-(verbose*10))

        exifs = []
        for inpath in paths:
            ### do something with inpath ###
            exifs.extend(import_images(inpath,recurse))
        create_kml(exifs, filename=outputfn)
        return 0
    except KeyboardInterrupt:
        ### handle keyboard interrupt ###
        return 0
    except Exception, e:
        if DEBUG or TESTRUN:

            raise(e)
        indent = len(program_name) * " "
        sys.stderr.write(program_name + ": " + repr(e) + "\n")
        sys.stderr.write(indent + "  for help use --help")
        return 2

if __name__ == "__main__":
    if DEBUG:
        sys.argv.append('-vv')
    if TESTRUN:
        import doctest
        doctest.testmod()
    if PROFILE:
        import cProfile
        import pstats
        profile_filename = 'Img2GE_profile.txt'
        cProfile.run('main()', profile_filename)
        statsfile = open("profile_stats.txt", "wb")
        p = pstats.Stats(profile_filename, stream=statsfile)
        stats = p.strip_dirs().sort_stats('cumulative')
        stats.print_stats()
        statsfile.close()
        sys.exit(0)
    sys.exit(main())