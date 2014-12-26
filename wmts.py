from __future__ import division
import tornado.ioloop
import tornado.web
from tornado.httpclient import AsyncHTTPClient
import pycurl
import math

AsyncHTTPClient.configure("tornado.curl_httpclient.CurlAsyncHTTPClient", max_clients=20)


class WMTSHandler(tornado.web.RequestHandler):

    url_pattern = {
        "google_street": "http://mt0.google.cn/vt/lyrs=m@169000000&hl=zh-CN&gl=cn&x=%s&y=%s&z=%s",
        "google_satellite": "http://mt0.google.cn/vt/lyrs=s&hl=zh-CN&gl=cn&x=%s&y=%s&z=%s",
        "tiandi_wgs84": "http://t2.tianditu.com/DataServer?T=vec_c&x=%s&y=%s&l=%s",
        "tiandi_mercator": "http://t2.tianditu.com/DataServer?T=vec_w&x=%s&y=%s&l=%s",
        "bing": "http://t1.tiles.ditu.live.com/tiles/r%s.png?g=100&mkt=zh-cn&n=z",
        "openstreet": "http://a.tile.openstreetmap.org/%s/%s/%s.png",
        "opencycle": "http://c.tile.opencyclemap.org/cycle/%s/%s/%s.png",
        "amap": "http://webrd02.is.autonavi.com/appmaptile?size=1&scale=1&style=7&x=%s&y=%s&z=%s",
        "tencent": "http://p1.map.gtimg.com/maptilesv2/%s/%s/%s/%s_%s.png",
        "here": "http://3.maps.nlp.nokia.com.cn/maptile/2.1/maptile/newest/normal.day/%s/%s/%s/256/png8?lg=CHI&app_id=90oGXsXHT8IRMSt5D79X&token=JY0BReev8ax1gIrHZZoqIg",
        "apple": "http://cdn-cn1.apple-mapkit.com/tp/2/tiles?x=%s&y=%s&z=%s&lang=zh-Hans&size=1&scale=1&style=0&vendorkey=546bccd01bb595c1ae74836bf94b56735aa7f907",
        "360": "http://map0.ishowchina.com/sotile/?x=%s&y=%s&z=%s&style=2&v=2",
        "supermap": "http://t1.supermapcloud.com/FileService/image?x=%s&y=%s&z=%s",
        "mapabc": "http://emap1.mapabc.com/mapabc/maptile?x=%s&y=%s&z=%s",
        "geoq": "http://map.geoq.cn/ArcGIS/rest/services/ChinaOnlineCommunity/MapServer/tile/%s/%s/%s",
        "51ditu": "http://cache5.51ditu.com/%s/%s%s.png",
        "baidu": "http://shangetu1.map.bdimg.com/it/u=x=%s;y=%s;z=%s;v=017;type=web&fm=44",
        "sogou": "http://p1.go2map.com/seamless1/0/174/%s/%s/%s/%s_%s.png"
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

        if row == -1 or col == -1 or level == -1:
            row = self.get_argument("TILEROW", -1)
            col = self.get_argument("TILECOL", -1)
            level = self.get_argument("TILEMATRIX", -1)
            layer = self.get_argument("LAYER", "google_street")

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

        def xy_to_51ditu(x, y, z):
            x -= pow(2, (z - 1))
            y = pow(2, (z - 1)) - 1 - y
            ce = int(math.ceil((z - 5) / 4))
            ve = 0
            be = 0
            ne = 0
            me = ""
            for _e in range(ce):
                Qe = 1 << (4 * (ce - _e))
                We = int((x - ve * ne) / Qe)
                Ee = int((y - be * ne) / Qe)
                me += (str(We) if (We > 9) else ("0" + str(We))) + (str(Ee) if (Ee > 9) else ("0" + str(Ee))) + "/"
                ve = We
                be = Ee
                ne = Qe
            Te = (((x) & ((1 << 20) - 1)) + (((y) & ((1 << 20) - 1)) * pow(2, 20)) + (((z) & ((1 << 8) - 1)) * pow(2, 40)))
            return me, Te

        if row != -1 and col != -1 and level != -1:
            if layer == "google_satellite":
                self.set_header("Content-Type", "image/jpeg")
            elif layer == "geoq":
                self.set_header("Content-Type", "image/jpg")
            else:
                self.set_header("Content-Type", "image/png")
            if layer == "bing":
                key = xy_to_bing(int(col), int(row), int(level))
                url = self.url_pattern.get(layer) % key
            elif layer == "openstreet" or layer == "opencycle" or layer == "here":
                url = self.url_pattern.get(layer) % (level, col, row)
            elif layer == "geoq":
                url = self.url_pattern.get(layer) % (level, row, col)
            elif layer == "tencent":
                new_row = pow(2, int(level)) - 1 - int(row)
                url = self.url_pattern.get(layer) % (level, str(int(col) // 16), str(new_row // 16), col, str(new_row))
            elif layer == "360":
                new_row = pow(2, int(level)) - 1 - int(row)
                url = self.url_pattern.get(layer) % (col, new_row, level)
            elif layer == "51ditu":
                url1, url2 = xy_to_51ditu(int(col), int(row), int(level))
                url = self.url_pattern.get(layer) % (level, url1, url2)
            elif layer == "baidu":
                offset = 3 * pow(2, (int(level) - 3))
                new_col = int(col) - offset
                new_row = offset - 1 - int(row)
                if new_col < 0:
                    new_col = 'M' + str(-new_col)
                else:
                    new_col = str(new_col)
                if new_row < 0:
                    new_row = 'M' + str(-new_row)
                else:
                    new_row = str(new_row)
                url = self.url_pattern.get(layer) % (new_col, new_row, level)
            elif layer == "sogou":
                offset = 3 * pow(2, (int(level) - 3))
                new_col = int(col) - offset
                new_row = offset - 1 - int(row)
                new_level = 729 - int(level)
                if new_level == 710:
                    new_level = 792
                factor_x = int(math.floor(new_col / 200))
                factor_y = int(math.floor(new_row / 200))
                if new_col < 0:
                    new_col = 'M' + str(-new_col)
                    factor_x = 'M' + str(-factor_x)
                else:
                    new_col = str(new_col)
                    factor_x = str(factor_x)
                if new_row < 0:
                    new_row = 'M' + str(-new_row)
                    factor_y = 'M' + str(-factor_y)
                else:
                    new_row = str(new_row)
                    factor_y = str(factor_y)
                url = self.url_pattern.get(layer) % (str(new_level), factor_x, factor_y, new_col, new_row)
            else:
                url = self.url_pattern.get(layer) % (col, row, level)
            print url

            client = AsyncHTTPClient()
            try:
                request = tornado.httpclient.HTTPRequest(url, request_timeout=3, user_agent=self.request.headers["User-Agent"])
            except:
                request = tornado.httpclient.HTTPRequest(url, request_timeout=3)

            client.fetch(request, self.write_response)

        else:
            self.set_header("Content-Type", "text/xml;charset=utf-8")
            self.write(open("wmts.xml").read())
            self.finish()

    post = get


application = tornado.web.Application([(r"/wmts", WMTSHandler)], "", None)

application.listen(5555)
tornado.ioloop.IOLoop.instance().start()
