# coding=utf-8
'''
Created on 2012-7-19
将google Map转化为WMST服务
@author: fiftyk
'''
import tornado.ioloop
import tornado.web
import sqlite3, StringIO, math
from tornado.web import GZipContentEncoding
from tornado.httpclient import AsyncHTTPClient
import pycurl

AsyncHTTPClient.configure("tornado.curl_httpclient.CurlAsyncHTTPClient", max_clients=20)


class WMTSHandler(tornado.web.RequestHandler):

    url_pattern = {
        "google_street": "http://mt0.google.cn/vt/lyrs=m@169000000&hl=zh-CN&gl=cn&x=%s&y=%s&z=%s",
        "google_satellite": "http://mt0.google.cn/vt/lyrs=s&hl=zh-CN&gl=cn&x=%s&y=%s&z=%s",
        "tiandi_wgs84": "http://t2.tianditu.com/DataServer?T=vec_c&x=%s&y=%s&l=%s",
        "tiandi_mercator": "http://t2.tianditu.com/DataServer?T=vec_w&x=%s&y=%s&l=%s",
        "bing": "http://t0.tiles.ditu.live.com/tiles/r%s.png?g=100&mkt=zh-cn&n=z",
        "openstreet": r"http://a.tile.openstreetmap.org/%s/%s/%s.png",
        "opencycle": r"http://c.tile.opencyclemap.org/cycle/%s/%s/%s.png"
    }

    def initialize(self):
        pass

    def write_response(self, res):
                if res.body is not None:
                    self.write(res.body)
                    self.finish()
                else:
                    print "FAIL"
                    self.finish()


    @tornado.web.asynchronous
    def get(self):
        print self.request.arguments
        # ?SERVICE=WMTS&VERSION=1.0.0&REQUEST=GetCapabilities
        # TileRow=1&TileCol=0
        row = self.get_argument("TileRow", -1)
        col = self.get_argument("TileCol", -1)
        level = self.get_argument("TileMatrix", -1)
        layer = self.get_argument("layer", "google_street")

        def xy_to_bing(x, y, z):
            quadkey = ""
            for i in range(z):
                digit = 0
                mask = 1 << i
                if x & mask != 0:
                    digit += 1
                if y & mask != 0:
                    digit += 2
                quadkey = str(digit) + quadkey
            return quadkey

        if row != -1 and col != -1 and level != -1:
            if layer == "satellite":
                self.set_header("Content-Type", "image/jpeg")
            else:
                self.set_header("Content-Type", "image/png")
            if layer == "bing":
                key = xy_to_bing(int(col), int(row), int(level))
                url = self.url_pattern.get(layer) % key
            elif layer == "openstreet" or layer == "opencycle":
                url = self.url_pattern.get(layer) % (level, col, row)
            else:
                url = self.url_pattern.get(layer) % (col, row, level)
            print url

            client = AsyncHTTPClient()
            try:
                request = tornado.httpclient.HTTPRequest(url, request_timeout=5, user_agent=self.request.headers["User-Agent"])
            except:
                request = tornado.httpclient.HTTPRequest(url, request_timeout=5)
            client.fetch(request, self.write_response)

        else:
            self.set_header("Content-Type", "text/xml;charset=utf-8")
            self.xml = open("wmts.xml").read()
            self.write(self.xml)
            self.finish()

    post = get

#GZipContentEncoding.CONTENT_TYPES.add("image/png")

application = tornado.web.Application([
                                          (r"/wmts", WMTSHandler)
                                      ], "", None)

application.listen(5555)
tornado.ioloop.IOLoop.instance().start()