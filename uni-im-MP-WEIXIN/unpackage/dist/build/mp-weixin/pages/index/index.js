"use strict";
const e = require("../../common/vendor.js"),
    i = require("../../uni_modules/uni-im/sdk/index.js"),
    t = {
        onLoad() {},
        onShow() {},
        computed: {
            isWidescreen: () => i.uniIm.isWidescreen
        },
        data: () => ({
            isOpenItemTitle: "",
            menuList: [{
                title: "个人中心",
                path: "/uni_modules/uni-id-pages/pages/userinfo/userinfo",
                srcName: "group"
            }, {
                title: "自助查码",
                path: "/pages/workbench/qrcode/qrcode",
                srcName: "qrCode"
            }]
        }),
        methods: {
            openPages(i) {
                this.isOpenItemTitle = i.title, e.index.navigateTo({
                    url: i.path,
                    fail: e => {
                        console.error(e, i.path)
                    }
                })
            }
        }
    };
if (!Array) {
    (e.resolveComponent("uni-list-item") + e.resolveComponent("uni-list"))()
}
Math || ((() => "../../uni_modules/uni-list/components/uni-list-item/uni-list-item.js") + (() => "../../uni_modules/uni-list/components/uni-list/uni-list.js"))();
const n = e._export_sfc(t, [
    ["render", function (i, t, n, s, o, r) {
        return {
            a: e.f(o.menuList, ((i, t, n) => ({
                a: "/static/" + i.srcName + ".png",
                b: t,
                c: e.o((e => r.openPages(i)), t),
                d: o.isOpenItemTitle === i.title ? 1 : "",
                e: "abbb8c9a-1-" + n + ",abbb8c9a-0",
                f: e.p({
                    title: i.title,
                    link: !0,
                    showBadge: !0
                })
            }))),
            b: e.p({
                border: !1
            })
        }
    }]
]);
wx.createPage(n);