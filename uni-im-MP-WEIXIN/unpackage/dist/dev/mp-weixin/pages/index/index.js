"use strict";
const common_vendor = require("../../common/vendor.js");
const uni_modules_uniIm_sdk_index = require("../../uni_modules/uni-im/sdk/index.js");
const _sfc_main = {
  onLoad() {
  },
  onShow() {
  },
  computed: {
    //是否为pc宽屏（width>960px）
    isWidescreen() {
      return uni_modules_uniIm_sdk_index.uniIm.isWidescreen;
    }
  },
  data() {
    return {
      isOpenItemTitle: "",
      menuList: [
        {
          title: "个人中心",
          path: "/uni_modules/uni-id-pages/pages/userinfo/userinfo",
          srcName: "group"
        },
        {
          title: "自助查码",
          path: "/pages/workbench/qrcode/qrcode",
          srcName: "qrCode"
        },
        // {
        // 	title: '付款专用',
        // 	path: '/pages/workbench/pay/pay',
        // 	srcName: 'notification'
        // },
        // {
        // 	title: '找人/找群',
        // 	path: '/uni_modules/uni-im/pages/contacts/addPeopleGroups/addPeopleGroups',
        // 	srcName: 'search'
        // },
        {
          title: "我的群聊",
          path: "/pages/workbench/groupList/groupList",
          srcName: "group"
        }
        // {
        // 	title: '创建群聊',
        // 	path: '/uni_modules/uni-im/pages/contacts/createGroup/createGroup',
        // 	srcName: 'createGroup'
        // },
      ]
    };
  },
  methods: {
    openPages(item) {
      this.isOpenItemTitle = item.title;
      common_vendor.index.navigateTo({
        url: item.path,
        fail: (e) => {
          common_vendor.index.__f__("error", "at pages/index/index.vue:86", e, item.path);
        }
      });
    },
    handleContact(e) {
      var _a, _b;
      common_vendor.index.__f__("log", "at pages/index/index.vue:91", "客服消息返回 path:", (_a = e == null ? void 0 : e.detail) == null ? void 0 : _a.path);
      common_vendor.index.__f__("log", "at pages/index/index.vue:92", "客服消息返回 query:", (_b = e == null ? void 0 : e.detail) == null ? void 0 : _b.query);
    },
    handleWxLogin() {
      const tmplIds = ["cTnevM68LHSasccywmgQ47tLkS0fgcTFevD2rTErYug"];
      if (!common_vendor.wx$1.requestSubscribeMessage) {
        common_vendor.index.__f__("log", "at pages/index/index.vue:98", "requestSubscribeMessage 失败:", {
          errMsg: "基础库版本过低，不支持 requestSubscribeMessage（需 ≥2.4.4）"
        });
        return;
      }
      const req = common_vendor.wx$1.requestSubscribeMessage({
        tmplIds
      });
      if (req && typeof req.then === "function") {
        req.then((res) => {
          common_vendor.index.__f__("log", "at pages/index/index.vue:109", "requestSubscribeMessage 成功:", res);
        }).catch((err) => {
          common_vendor.index.__f__("log", "at pages/index/index.vue:112", "requestSubscribeMessage 失败:", err);
        });
      } else {
        common_vendor.wx$1.requestSubscribeMessage({
          tmplIds,
          success: (res) => {
            common_vendor.index.__f__("log", "at pages/index/index.vue:118", "requestSubscribeMessage 成功:", res);
          },
          fail: (err) => {
            common_vendor.index.__f__("log", "at pages/index/index.vue:121", "requestSubscribeMessage 失败:", err);
          }
        });
      }
    }
  }
};
if (!Array) {
  const _easycom_uni_list_item2 = common_vendor.resolveComponent("uni-list-item");
  const _easycom_uni_list2 = common_vendor.resolveComponent("uni-list");
  (_easycom_uni_list_item2 + _easycom_uni_list2)();
}
const _easycom_uni_list_item = () => "../../uni_modules/uni-list/components/uni-list-item/uni-list-item.js";
const _easycom_uni_list = () => "../../uni_modules/uni-list/components/uni-list/uni-list.js";
if (!Math) {
  (_easycom_uni_list_item + _easycom_uni_list)();
}
function _sfc_render(_ctx, _cache, $props, $setup, $data, $options) {
  return {
    a: common_vendor.f($data.menuList, (menu, menuIndex, i0) => {
      return {
        a: "/static/" + menu.srcName + ".png",
        b: menuIndex,
        c: common_vendor.o(($event) => $options.openPages(menu), menuIndex),
        d: $data.isOpenItemTitle === menu.title ? 1 : "",
        e: "66f2f270-1-" + i0 + ",66f2f270-0",
        f: common_vendor.p({
          title: menu.title,
          link: true,
          showBadge: true
        })
      };
    }),
    b: common_vendor.p({
      border: false
    }),
    c: common_vendor.o((...args) => $options.handleContact && $options.handleContact(...args), "3f"),
    d: common_vendor.o((...args) => $options.handleWxLogin && $options.handleWxLogin(...args), "c7")
  };
}
const MiniProgramPage = /* @__PURE__ */ common_vendor._export_sfc(_sfc_main, [["render", _sfc_render]]);
wx.createPage(MiniProgramPage);
//# sourceMappingURL=../../../.sourcemap/mp-weixin/pages/index/index.js.map
