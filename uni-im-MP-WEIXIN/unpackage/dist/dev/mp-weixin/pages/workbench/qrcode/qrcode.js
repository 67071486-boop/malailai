"use strict";
var __async = (__this, __arguments, generator) => {
  return new Promise((resolve, reject) => {
    var fulfilled = (value) => {
      try {
        step(generator.next(value));
      } catch (e) {
        reject(e);
      }
    };
    var rejected = (value) => {
      try {
        step(generator.throw(value));
      } catch (e) {
        reject(e);
      }
    };
    var step = (x) => x.done ? resolve(x.value) : Promise.resolve(x.value).then(fulfilled, rejected);
    step((generator = generator.apply(__this, __arguments)).next());
  });
};
const common_vendor = require("../../../common/vendor.js");
const uni_modules_uniIdPages_common_store = require("../../../uni_modules/uni-id-pages/common/store.js");
const _sfc_main = {
  name: "OrderGroupCode",
  // 组件名（后续父组件注册要用）
  props: {
    // 可选：接收父组件传递的参数
    param: {
      type: Object,
      default: () => ({})
    }
  },
  data() {
    return {
      orderNo: "",
      // 订单号输入值
      qrcodeSrc: "",
      // 二维码图片地址
      loading: false,
      // 查询加载状态
      errorMsg: "",
      // 错误提示文本
      userInfo: {}
      // 当前用户信息（需确保该字段已正确赋值，如从uniId/缓存获取）
    };
  },
  methods: {
    setParam(param) {
      common_vendor.index.__f__("log", "at pages/workbench/qrcode/qrcode.vue:71", "自助查码组件接收参数：", param);
    },
    /**
     * 清空错误提示（输入框输入时触发）
     */
    clearError() {
      this.errorMsg = "";
    },
    /**
     * 处理二维码图片加载失败
     */
    handleImgError() {
      this.errorMsg = "二维码图片加载失败，请重试";
      this.qrcodeSrc = "";
    },
    /**
     * 校验订单号格式：纯数字且长度≥15位
     * @param {string} content - 待校验的订单号
     * @returns {boolean} 校验结果
     */
    validateOrderNo(content) {
      if (typeof content !== "string")
        return false;
      const pureContent = content.trim();
      if (!pureContent)
        return false;
      const numberReg = /^\d+$/;
      if (!numberReg.test(pureContent))
        return false;
      if (pureContent.length < 15)
        return false;
      return true;
    },
    confiremQueryQrcode() {
      common_vendor.index.showModal({
        title: "警告",
        // 对话框标题
        content: "请确认该笔订单由你本人接手，恶意查询将被封禁",
        // 提示文字
        cancelText: "取消",
        // 取消按钮文字
        confirmText: "查询",
        // 确认按钮文字
        success: (res) => {
          if (res.confirm) {
            this.queryQrcode();
          } else if (res.cancel) {
            common_vendor.index.showToast({
              title: "已取消操作",
              icon: "none",
              duration: 1500
            });
          }
        }
      });
    },
    /**
     * 核心逻辑：调用云函数查询二维码
     */
    queryQrcode() {
      return __async(this, null, function* () {
        this.userInfo = uni_modules_uniIdPages_common_store.store.userInfo;
        const orderNo = this.orderNo.trim();
        if (!orderNo) {
          this.errorMsg = "请输入订单号";
          return;
        }
        if (!this.validateOrderNo(orderNo)) {
          this.errorMsg = "订单号必须为纯数字且长度不低于15位";
          return;
        }
        this.loading = true;
        this.errorMsg = "";
        this.qrcodeSrc = "";
        try {
          const cloudRes = yield common_vendor._r.callFunction({
            name: "queryGroupQrcode",
            // 云函数名称（需与部署的一致）
            data: {
              orderNo,
              qr_code: "true",
              booster: this.userInfo.nickname
            }
            // 传递给云函数的参数
          });
          const {
            code,
            data,
            msg
          } = cloudRes.result;
          if (code === 200) {
            if (Array.isArray(data) && data.length > 0) {
              if (data[0].join_qr_code) {
                this.qrcodeSrc = data[0].join_qr_code;
                this.errorMsg = "二维码绑定成功，截图后使用微信扫码进群11";
              } else {
                this.errorMsg = "未查询到该订单对应的二维码，联系售后客服";
              }
            }
          } else {
            this.errorMsg = msg || "系统接口错误，请稍后重试";
          }
        } catch (error) {
          this.errorMsg = `查询失败：${error.message || "系统异常，请稍后重试"}`;
          common_vendor.index.__f__("error", "at pages/workbench/qrcode/qrcode.vue:198", "查询二维码异常：", error);
        } finally {
          this.loading = false;
        }
      });
    }
  }
};
function _sfc_render(_ctx, _cache, $props, $setup, $data, $options) {
  return common_vendor.e({
    a: !_ctx.uniIDHasRole("visitor")
  }, !_ctx.uniIDHasRole("visitor") ? common_vendor.e({
    b: common_vendor.o([($event) => $data.orderNo = $event.detail.value, (...args) => $options.clearError && $options.clearError(...args)], "1c"),
    c: $data.orderNo,
    d: $data.loading
  }, $data.loading ? {} : {}, {
    e: common_vendor.o((...args) => $options.confiremQueryQrcode && $options.confiremQueryQrcode(...args), "4b"),
    f: $data.loading || !$data.orderNo.trim(),
    g: $data.errorMsg
  }, $data.errorMsg ? {
    h: common_vendor.t($data.errorMsg)
  } : {}, {
    i: !$data.qrcodeSrc && !$data.loading && !$data.errorMsg
  }, !$data.qrcodeSrc && !$data.loading && !$data.errorMsg ? {} : {}, {
    j: $data.loading
  }, $data.loading ? {} : {}, {
    k: $data.qrcodeSrc
  }, $data.qrcodeSrc ? {
    l: $data.qrcodeSrc,
    m: common_vendor.o((...args) => $options.handleImgError && $options.handleImgError(...args), "8d")
  } : {}) : {});
}
const MiniProgramPage = /* @__PURE__ */ common_vendor._export_sfc(_sfc_main, [["render", _sfc_render], ["__scopeId", "data-v-d0ac87b1"]]);
wx.createPage(MiniProgramPage);
//# sourceMappingURL=../../../../.sourcemap/mp-weixin/pages/workbench/qrcode/qrcode.js.map
