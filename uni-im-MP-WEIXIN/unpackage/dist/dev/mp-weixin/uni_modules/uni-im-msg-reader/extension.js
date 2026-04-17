"use strict";
var __defProp = Object.defineProperty;
var __defProps = Object.defineProperties;
var __getOwnPropDescs = Object.getOwnPropertyDescriptors;
var __getOwnPropSymbols = Object.getOwnPropertySymbols;
var __hasOwnProp = Object.prototype.hasOwnProperty;
var __propIsEnum = Object.prototype.propertyIsEnumerable;
var __defNormalProp = (obj, key, value) => key in obj ? __defProp(obj, key, { enumerable: true, configurable: true, writable: true, value }) : obj[key] = value;
var __spreadValues = (a, b) => {
  for (var prop in b || (b = {}))
    if (__hasOwnProp.call(b, prop))
      __defNormalProp(a, prop, b[prop]);
  if (__getOwnPropSymbols)
    for (var prop of __getOwnPropSymbols(b)) {
      if (__propIsEnum.call(b, prop))
        __defNormalProp(a, prop, b[prop]);
    }
  return a;
};
var __spreadProps = (a, b) => __defProps(a, __getOwnPropDescs(b));
const common_vendor = require("../../common/vendor.js");
const uni_modules_uniIm_sdk_index = require("../uni-im/sdk/index.js");
({
  name: "UniImMsgReader",
  props: {
    msg: {
      type: Object,
      default: () => {
      }
    },
    hiddenState: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      showPopup: false,
      showTransition: false,
      conversation: {},
      currentIndex: 0
    };
  },
  // 计算属性
  computed: __spreadProps(__spreadValues({}, uni_modules_uniIm_sdk_index.uniIm.mapState(["isWidescreen", "systemInfo"])), {
    currentUid() {
      return uni_modules_uniIm_sdk_index.uniIm.currentUser._id;
    },
    isReady() {
      var _a, _b;
      return !((_b = (_a = this.conversation.group) == null ? void 0 : _a.member) == null ? void 0 : _b.hasMore);
    },
    memberUids() {
      var _a;
      const groupMember = (_a = this.conversation.group) == null ? void 0 : _a.member;
      if (groupMember) {
        return groupMember.dataList.filter((item) => item.users._id != this.msg.from_uid).map((item) => item.users._id);
      } else {
        return [];
      }
    },
    unreadUserList() {
      const unreadUserList = this.memberUids.filter((item) => !this.readerList.find((reader) => reader.user_id == item));
      return unreadUserList.map((item) => uni_modules_uniIm_sdk_index.uniIm.users[item]);
    },
    unreadUserCountTip() {
      let unreadUserCount = this.unreadUserList.length;
      unreadUserCount = unreadUserCount > 99 ? "99+" : unreadUserCount;
      return unreadUserCount > 0 ? `${unreadUserCount}人未读` : "全部已读";
    },
    isGroupMsg() {
      return !!this.msg.group_id;
    },
    readerList() {
      return this.msg.reader_list || [];
    },
    readerUserlist() {
      return this.readerList.map((item) => uni_modules_uniIm_sdk_index.uniIm.users[item.user_id]);
    }
  }),
  watch: {
    showPopup(state) {
      setTimeout(() => {
        this.showTransition = state;
      }, 0);
    }
  },
  mounted() {
    this.conversation = uni_modules_uniIm_sdk_index.uniIm.conversation.find(this.msg.conversation_id);
  },
  methods: {
    clickHandler() {
      if (this.isGroupMsg) {
        if (uni_modules_uniIm_sdk_index.uniIm.isWidescreen) {
          this.showReaderList();
        } else {
          common_vendor.index.navigateTo({
            url: `/uni_modules/uni-im-msg-reader/pages/reader-list/reader-list?msgId=${this.msg._id}&conversationId=${this.msg.conversation_id}`
            // animationType: 'slide-in-bottom'
          });
        }
      }
    },
    showReaderList() {
      this.showPopup = true;
    },
    closePopup() {
      this.showPopup = false;
    }
  }
});
if (!Array) {
  const _easycom_uni_segmented_control2 = common_vendor.resolveComponent("uni-segmented-control");
  const _easycom_cloud_image2 = common_vendor.resolveComponent("cloud-image");
  (_easycom_uni_segmented_control2 + _easycom_cloud_image2)();
}
const _easycom_uni_segmented_control = () => "../uni-segmented-control/components/uni-segmented-control/uni-segmented-control.js";
const _easycom_cloud_image = () => "../uni-id-pages/components/cloud-image/cloud-image.js";
if (!Math) {
  (_easycom_uni_segmented_control + _easycom_cloud_image)();
}
//# sourceMappingURL=../../../.sourcemap/mp-weixin/uni_modules/uni-im-msg-reader/extension.js.map
