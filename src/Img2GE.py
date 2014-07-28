#!/usr/local/bin/python2.7
# encoding: utf-8
'''
Img2GE -- Plot local images w/ GPS data onto Google Earth VIA crafted .kml

Img2GE is a small script that plots local images w/ GPS data onto Google Earth VIA crafted .kml

Dependencies:
    exifread - https://pypi.python.org/pypi/ExifRead
    simplekml - https://pypi.python.org/pypi/simplekml

@author:     Daniel Gordon

@copyright:  2014 Daniel Gordon. All rights reserved.

@license:    GPL3

@contact:    ac3d912@yahoo.com
@deffield    updated: Updated
'''

from argparse import ArgumentParser, RawDescriptionHelpFormatter
from itertools import groupby
from logging import getLogger, basicConfig, INFO
from Versioning import Version
import os
import sys

import exifread
import simplekml
if Version(simplekml.__version__) < "1.3":
    print "Requires simplekml version 1.3+.  You have: %s" % simplekml.__version__
    sys.exit(-1)
import math

#Just adding a little convenience functionality to the exifread's Ratio class 
def decimal(self):
        if self.den > 0:
            return float(self.num) / self.den
        else:
            return 0
exifread.Ratio.decimal = decimal 

basicConfig(format="%(message)s")
log = getLogger()
log.setLevel(INFO)

__all__ = []
__version__ = 0.2
__date__ = '2014-07-22'
__updated__ = '2014-07-22'
__license__ = "GPL3"

DEBUG = 0
TESTRUN = 0
PROFILE = 0

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
    @return: list of exifs
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
    '''
    Get the coordinate data from exif data
    
    @return: (longitude, latitude) -- both in +/- decimal fmt
    '''
    if not ('GPS GPSLongitude' in exif and 'GPS GPSLatitude' in exif):
        return (0,0)  
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
    count = 0
    for grp_name, exifs in groupby(exifs,key=lambda x:os.path.dirname(x['Filename'])):
        folder_created = False
        for exif in exifs:
            log.debug(str(exif))
            if 'GPS GPSLatitude' in exif and 'GPS GPSLongitude' in exif:
                count += 1
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
                photo.style.iconstyle.heading = hdg
                #Calculate this based upon the proper orientation (portrait/landscape) of the image
                aspratio = float(exif['EXIF ExifImageWidth'].values[0]) / exif['EXIF ExifImageLength'].values[0]
                efl = exif.get('EXIF FocalLengthIn35mmFilm',None)
                if efl is not None:
                    efl = efl.values[0]
                else:   efl = 35
                horiz = math.degrees(2*math.atan(24.0/(2*efl)))/2
                vert = math.degrees(2*math.atan((24.0/aspratio)/(2*efl)))/2
                photo.viewvolume = simplekml.ViewVolume(-1 * horiz, horiz, -1 * vert, vert,50)
                photo.point.coords = [coords]
    log.info("Found %s images with coords."%count)
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

    Copyright (C) %s  Daniel Gordon

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
    
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