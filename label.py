#!/usr/bin/env python
# coding: utf-8

import subprocess
import os
import platform
import sys
from math import pi, atan2


sys.path.append('/usr/share/inkscape/extensions')
import inkex
import simplepath
import simplestyle
from simpletransform import parseTransform, applyTransformToNode


def get_n_points_from_path(node, n):
    """returns a list of first n points (x,y) in an SVG path-representing node"""
    p = simplepath.parsePath(node.get('d'))
    xi = []
    yi = []
    for cmd,params in p:
        defs = simplepath.pathdefs[cmd]
        for i in range(defs[1]):
            if   defs[3][i] == 'x' and len(xi) < n:
                xi.append(params[i])
            elif defs[3][i] == 'y' and len(yi) < n:
                yi.append(params[i])

    if len(xi) == n and len(yi) == n:
        points = []
        for i in range(n):
            points.append( (xi[i], yi[i]) )
    else:
        return []
    return points



TEMPLATE = u"""<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg
   xmlns:dc="http://purl.org/dc/elements/1.1/"
   xmlns:cc="http://creativecommons.org/ns#"
   xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
   xmlns:svg="http://www.w3.org/2000/svg"
   xmlns="http://www.w3.org/2000/svg"
   xmlns:sodipodi="http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"
   xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"
   width="744.09448819"
   height="1052.3622047"
   id="svg5856"
   version="1.1">
   {tag}
</svg>
"""

def text_bbox(text):
    """Hack to compute height and with of a text in units of the document.
     Works by constructing SVG and asking Inkscape."""

    if platform.system() == 'Darwin':
        inkscape = '/Applications/Inkscape.app/Contents/Resources/bin/inkscape'
    else:
        inkscape = 'inkscape'

    svg = TEMPLATE.format(tag=text)
    try:
        with open('/tmp/bullshit.svg','w') as fp:
            fp.write(svg.encode('utf-8'))
        w = float(subprocess.check_output([inkscape, '-z', '-D', '-f', '/tmp/bullshit.svg', '-W']))
        h = float(subprocess.check_output([inkscape, '-z', '-D', '-f', '/tmp/bullshit.svg', '-H']))
    finally:
        os.remove("/tmp/bullshit.svg")
    return w, h


class Label(inkex.Effect):
    def __init__(self):
        inkex.Effect.__init__(self)
        self.OptionParser.add_option("-t", "--text",
                                     action="store", type="string",
                                     dest="text", default='',
                                     help="Text put on label")
        self.OptionParser.add_option("-f", "--font-family",
                                     action="store", type="string",
                                     dest="font_family", default='',
                                     help="Font to use")
        self.OptionParser.add_option("-s", "--font-size",
                                     action="store", type="string",
                                     dest="font_size", default='',
                                     help="Font size")
        self.OptionParser.add_option("--font-color",
                                     action="store", type="string",
                                     dest="font_color", default='',
                                     help="color of label font")
        self.OptionParser.add_option("-c", "--background-color",
                                     action="store", type="string",
                                     dest="background_color", default='',
                                     help="color of label background")
        self.OptionParser.add_option("-o", "--background-opacity",
                                     action="store", type="string",
                                     dest="background_opacity", default='',
                                     help="opacity of label background")
        self.OptionParser.add_option("--stroke-width-1",
                                     action="store", type="string",
                                     dest="stroke_width_1", default='',
                                     help="Width of leader 1")
        self.OptionParser.add_option("--stroke-width-2",
                                     action="store", type="string",
                                     dest="stroke_width_2", default='',
                                     help="Width of leader 2")
        self.OptionParser.add_option("--stroke-color-1",
                                     action="store", type="string",
                                     dest="stroke_color_1", default='',
                                     help="Color code of leader 1 or hex color")
        self.OptionParser.add_option("--stroke-color-2",
                                     action="store", type="string",
                                     dest="stroke_color_2", default='',
                                     help="Color code of leader 2 or hex color")

    def make_text(self, anchor='start'):
        options = self.options
        font_size = float(options.font_size)
        style = {
            'font-size': options.font_size,
            'font-family': options.font_family,
            'text-anchor': anchor,
            'text-align': 'left',
            'fill': simplestyle.svgcolors[options.font_color]}
        
        formated_style =  simplestyle.formatStyle(style)
        txt_atts = {'style': formated_style,
                    'x': str(0.0),
                    'y': str(font_size*0.4),
                    inkex.addNS('space', 'xml'): 'preserve',}
        t = inkex.etree.Element('text', txt_atts)
        t.text = options.text.decode('utf-8')
        t_w, t_h = text_bbox(inkex.etree.tostring(t))
        return t, t_w, t_h
    

    def make_box(self, x, y, w, h, r):
        opt = self.options
        style_box = {
            'fill': simplestyle.svgcolors[opt.background_color],
            'fill-opacity': opt.background_opacity,
            'stroke': 'none',}
        rect_atts = {
            'style': simplestyle.formatStyle(style_box),
            'width': str(w),
            'height': str(h),
            'x': str(x),
            'y': str(y),
            'ry': str(r),}
        return inkex.etree.Element('rect', rect_atts)


    def make_double_line(self, length):
        opt = self.options
        
        w1 = float(opt.stroke_width_1)
        w2 = float(opt.stroke_width_2)
        offset = 0.5*(w1 + w2)

        line = inkex.etree.Element('g')

        style_line1 = {
                'fill': 'none',
                'stroke': simplestyle.svgcolors[opt.stroke_color_1],
                'stroke-width': opt.stroke_width_1,}
        path_atts_1 = {
            inkex.addNS('connector-curvature', 'inkscape'): "0",
            'd': "M 0.0,0.0 %f,0.0" % (length,),
            'style': simplestyle.formatStyle(style_line1), }
        inkex.etree.SubElement(line, 'path', path_atts_1)

        style_line2 = {
                'fill': 'none',
                'stroke': simplestyle.svgcolors[opt.stroke_color_2],
                'stroke-width': opt.stroke_width_2,}
        path_atts_2 = {
            inkex.addNS('connector-curvature', 'inkscape'): "0",
            'd': "M 0.0,%f %f,%f.0" % (offset, length, offset),
            'style': simplestyle.formatStyle(style_line2),}
        inkex.etree.SubElement(line, 'path', path_atts_2)
            
        return line


    def effect(self):
        pts = []
        for node in self.selected.itervalues():
            if node.tag == inkex.addNS('path','svg'):
                guide = node
                pts = get_n_points_from_path(node, 2)

        if len(pts) == 2:
    
            (x0, y0), (x1, y1) = pts
            theta = atan2(y1-y0, x1-x0)*180./pi
            length = ((x1-x0)**2 + (y1-y0)**2)**0.5
            
            label = inkex.etree.SubElement(self.current_layer, 'g')
            labeltag = inkex.etree.SubElement(label, 'g')
            
            
            if theta <= -90.0 or theta > 90.0:
                text, tw, th = self.make_text(anchor='end')
                applyTransformToNode(parseTransform('rotate(180.0)'), text)
            else:
                text, tw, th = self.make_text(anchor='start')
            
            fs = float(self.options.font_size)
            kh = 1.05
            h = kh*fs
            pad = (h - fs)*0.5 + 0.04*tw
            w = tw + pad*2
            x = -pad + 0.07*fs
            y = -0.5*h

            box = self.make_box(x, y, w, h, r=0.25*min(w, h))

            labeltag.append(box)
            labeltag.append(text)

            transform = 'translate(%f, 0.0)'% (length,)
            applyTransformToNode(parseTransform(transform), labeltag)
            
            leader = self.make_double_line(length+x)
            label.append(leader)

            transform = 'translate(%f, %f) rotate(%f)'%(x0, y0, theta)
            applyTransformToNode(parseTransform(transform), label)
        
            guide.getparent().remove(guide)


if __name__ == '__main__':
    e = Label()
    e.affect()
