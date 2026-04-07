<template>
	<view>
		<uni-list :border="false" class="menu-list-box">
			<uni-list-item v-for="(menu,menuIndex) in menuList" :key="menuIndex" :title="menu.title" link
				@click="openPages(menu)" :showBadge="true" :class="{activeMenu:isOpenItemTitle === menu.title}">
				<template v-slot:header>
					<view class="slot-icon-box green">
						<image class="slot-icon" :src="'/static/' + menu.srcName + '.png'" mode="widthFix"></image>
					</view>
				</template>
			</uni-list-item>
		</uni-list>
		<view class="contact-btn-wrap">
			<button class="contact-btn" open-type="contact" @contact="handleContact">联系客服</button>
			<button class="login-btn" @click="handleWxLogin">订阅</button>
		</view>
	</view>
</template>

<script>
	import uniIm from '@/uni_modules/uni-im/sdk/index.js';
	export default {
		onLoad() {},
		onShow() {},
		computed: {
			//是否为pc宽屏（width>960px）
			isWidescreen() {
				return uniIm.isWidescreen
			}
		},
		data() {
			return {
				isOpenItemTitle: '',
				menuList: [{
						title: '个人中心',
						path: '/uni_modules/uni-id-pages/pages/userinfo/userinfo',
						srcName: 'group'
					},
					{
						title: '自助查码',
						path: '/pages/workbench/qrcode/qrcode',
						srcName: 'qrCode'
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
					// {
					// 	title: '我的群聊',
					// 	path: '/uni_modules/uni-im/pages/contacts/groupList/groupList',
					// 	srcName: 'group'
					// },
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

				this.isOpenItemTitle = item.title
				// #ifdef H5
				if (this.isWidescreen) {
					let componentName = 'uni-im-' + item.path.split('/')[1],
						param = item.param
					return this.$emit('clickMenu', {
						componentName,
						param,
						title: item.title
					})
				}
				// #endif
				// console.log('item',item);
				uni.navigateTo({
					url: item.path,
					fail: (e) => {
						console.error(e, item.path);
					}
				})
			},
			handleContact(e) {
				console.log('客服消息返回 path:', e?.detail?.path)
				console.log('客服消息返回 query:', e?.detail?.query)
			},
			handleWxLogin() {
				const tmplIds = ['cTnevM68LHSasccywmgQ47tLkS0fgcTFevD2rTErYug'];
				// #ifdef MP-WEIXIN
				if (!wx.requestSubscribeMessage) {
					console.log('requestSubscribeMessage 失败:', {
						errMsg: '基础库版本过低，不支持 requestSubscribeMessage（需 ≥2.4.4）'
					});
					return;
				}
				const req = wx.requestSubscribeMessage({ tmplIds });
				if (req && typeof req.then === 'function') {
					req
						.then((res) => {
							console.log('requestSubscribeMessage 成功:', res);
						})
						.catch((err) => {
							console.log('requestSubscribeMessage 失败:', err);
						});
				} else {
					wx.requestSubscribeMessage({
						tmplIds,
						success: (res) => {
							console.log('requestSubscribeMessage 成功:', res);
						},
						fail: (err) => {
							console.log('requestSubscribeMessage 失败:', err);
						}
					});
				}
				// #endif
				// #ifndef MP-WEIXIN
				console.log('requestSubscribeMessage 失败: 仅微信小程序环境可用');
				// #endif
			},
		}
	}
</script>

<style lang="scss">
	@import "@/uni_modules/uni-im/common/baseStyle.scss";

	.menu-list-box {
		.uni-list-item {
			cursor: pointer;
			width: 750rpx;
			box-sizing: border-box;

			&:hover {
				background-color: #FBFBFB !important;
			}
		}
	}

	.contact-btn-wrap {
		padding: 24rpx;
	}

	.contact-btn {
		background-color: #07c160;
		color: #ffffff;
		border-radius: 12rpx;
		font-size: 30rpx;
	}

	.login-btn {
		margin-top: 20rpx;
		background-color: #1677ff;
		color: #ffffff;
		border-radius: 12rpx;
		font-size: 30rpx;
	}

	.slot-icon-box {
		width: 45px;
		height: 45px;
		align-items: center;
		justify-content: center;
		border-radius: 10rpx;
		margin-right: 20rpx;
	}

	.slot-icon {
		width: 30px;
		height: 30px;
	}

	.green {
		background-color: #08C060;
	}

	.title {
		padding: 8px;
		font-size: 14px;
		color: #999999;
	}
</style>