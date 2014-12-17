#!/usr/bin/env python
# coding: utf-8

import subprocess
import os
import sys
from math import pi, atan2


sys.path.append('/usr/share/inkscape/extensions')
import inkex
import simplepath
import simplestyle
import simpletransform

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
    """Hack to compute height and with of a text in units of px.
     Works by constructing SVG and asking Inkscape."""
    svg = TEMPLATE.format(tag=text)
    with open('/tmp/bullshit.svg','w') as fp:
        fp.write(svg.encode('utf-8'))
    w = float(subprocess.check_output("inkscape -z -D -f /tmp/bullshit.svg -W".split()))
    h = float(subprocess.check_output("inkscape -z -D -f /tmp/bullshit.svg -H".split()))
    os.remove("/tmp/bullshit.svg")
    return w, h
  

class Label(inkex.Effect):
    def __init__(self):
        inkex.Effect.__init__(self)
        self.OptionParser.add_option("-d", "--text",
                                     action="store", type="string",
                                     dest="text", default='??? MPa',
                                     help="Text put on label")
        self.OptionParser.add_option("-o", "--opacity",
                                     action="store", type="string",
                                     dest="opacity", default='70.0',
                                     help="opacity of label background")


    def _make_text(self):
        self.style_text = {
            'font-size': str(self.doc_h/30) + 'px',
            'font-family': 'Sans',
            'text-anchor': 'start',
            'text-align': 'left',
            'fill': simplestyle.svgcolors['black']}

        formated_style =  simplestyle.formatStyle(self.style_text)
        txt_atts = {'style': formated_style,
                    'x': str(0.0),
                    'y': str(0.0),
                    inkex.addNS('space', 'xml'): 'preserve',}
        self.t = inkex.etree.Element('text', txt_atts)
        self.t.text = self.options.text


    def _add_box(self):
        t_w, t_h = text_bbox(inkex.etree.tostring(self.t))
        self.t_w, self.t_h = t_w, t_h
        self.t.set('x', str(0.03*t_w))
        self.t.set('y', str(-0.5*(-1.15*t_h + 0.075*t_h)))
        rect_atts = {
            'style': "fill:#ffffff;fill-opacity:0.7;stroke:none",
            'width': str(1.08*t_w),
            'height': str(1.15*t_h),
            'x': "0.0",
            'y': str(0.5*(-1.15*t_h + 0.075*t_h)),
            'ry': str(0.25*min(t_w, t_h)),}
        self.box = inkex.etree.SubElement(self.inner_label_tag, 'rect', rect_atts)


    def _add_leader(self):
        path_atts0 = {
            inkex.addNS('connector-curvature', 'inkscape'): "0",
            'd': "M 0.0,0.0 %f,0.0" % (self.leader_length,),
            'style':"fill:none;stroke:#000000;stroke-width:2px;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1",}
        path_atts1 = {
            inkex.addNS('connector-curvature', 'inkscape'): "0",
            'd': "M 0.0,2.0 %f,2.0" % (self.leader_length,),
            'style':"fill:none;stroke:#ffffff;stroke-width:2px;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1",}
        self.leader = inkex.etree.SubElement(self.label, 'g')
        inkex.etree.SubElement(self.leader, 'path', path_atts0)
        inkex.etree.SubElement(self.leader, 'path', path_atts1)


    def effect(self):
        pts = []
        for node in self.selected.itervalues():
            if node.tag == inkex.addNS('path','svg'):
                lead = node
                pts = get_n_points_from_path(node, 2)

        if len(pts) == 2:

            (self.x0, self.y0), (self.x1, self.y1) = pts

            theta = atan2(self.y1-self.y0, self.x1-self.x0)*180./pi
            self.leader_length = ((self.x1-self.x0)**2 + (self.y1-self.y0)**2)**0.5

            parent = self.document.getroot()

            self.doc_w = inkex.unittouu(parent.get('width'))
            self.doc_h = inkex.unittouu(parent.get('height'))

            self.label = inkex.etree.SubElement(self.current_layer, 'g')
            self.labeltag = inkex.etree.SubElement(self.label, 'g')
            self.inner_label_tag = inkex.etree.SubElement(self.labeltag, 'g')

            self._make_text()
            self._add_box()
            self.inner_label_tag.append(self.t)     

            if theta <= -90.0 or theta > 90.0:
                transformation = 'translate(%s, 0.0) rotate(180.0)'% (self.box.get('width'),)
                transform = simpletransform.parseTransform(transformation)
                simpletransform.applyTransformToNode(transform, self.inner_label_tag)

            transformation = 'translate(%f, %f)'% (self.leader_length, 0.0)
            transform = simpletransform.parseTransform(transformation)
            simpletransform.applyTransformToNode(transform, self.labeltag)

            self._add_leader()
            transformation = 'translate(%f, %f) rotate(%f)'% (self.x0, self.y0, theta)
            transform = simpletransform.parseTransform(transformation)
            simpletransform.applyTransformToNode(transform, self.label)

            lead.getparent().remove(lead)


if __name__ == '__main__':

    e = Label()
    e.affect()

