<template>
	<view class="qrcode-query-page" v-if="!uniIDHasRole('visitor')">
		<!-- 顶部查询区域 -->
		<view class="query-header">
			<view class="input-group">
				<!-- 优化：仅允许输入数字，提升体验 -->
				<input v-model="orderNo" type="digit" pattern="[0-9]*" placeholder="请输入订单号查询群二维码" class="order-input"
					placeholder-class="input-placeholder" @input="clearError" />
				<button class="query-btn" @click="confiremQueryQrcode" :disabled="loading || !orderNo.trim()">
					<text v-if="loading">查询中...</text>
					<text v-else>查询</text>
				</button>
			</view>
			<!-- 错误提示 -->
			<view class="error-tip" v-if="errorMsg">{{ errorMsg }}</view>
		</view>

		<!-- 底部内容区域：二维码 + 注意事项 -->
		<view class="content-container">
			<!-- 二维码展示模块 -->
			<view class="qrcode-card">
				<!-- 空状态 -->
				<view class="empty-state" v-if="!qrcodeSrc && !loading && !errorMsg">
					暂无二维码，请输入订单号查询
				</view>
				<!-- 加载状态 -->
				<view class="loading-state" v-if="loading">
					<text>正在查询，请稍候...</text>
				</view>
				<!-- 二维码图片 -->
				<image v-if="qrcodeSrc" :src="qrcodeSrc" class="qrcode-img" mode="widthFix" lazy-load
					@error="handleImgError" />
			</view>

			<!-- 查询前注意事项（独立模块，固定显示） -->
			<view class="notice-card">
				<view class="notice-title">⚠️ 重要提醒</view>
				<view class="notice-content">
					[此功能测试中-]群聊二维码首次被查询后，将与打手绑定，其他打手无法继续查询，查询前请确保该订单属于自己接手。所有查询记录均保存在后台，禁止恶意查询二维码，屡次不改的0结算清退。
				</view>
			</view>
		</view>
	</view>
</template>

<script>
	import {
		store
	} from '@/uni_modules/uni-id-pages/common/store.js'
	export default {
		name: "OrderGroupCode", // 组件名（后续父组件注册要用）
		props: {
			// 可选：接收父组件传递的参数
			param: {
				type: Object,
				default: () => ({})
			}
		},
		data() {
			return {
				orderNo: "", // 订单号输入值
				qrcodeSrc: "", // 二维码图片地址
				loading: false, // 查询加载状态
				errorMsg: "", // 错误提示文本
				userInfo: {}, // 当前用户信息（需确保该字段已正确赋值，如从uniId/缓存获取）
			};
		},
		methods: {
			setParam(param) {
				// 可选：处理父组件传递的参数（根据业务需求写逻辑）
				console.log("自助查码组件接收参数：", param);
				// 这里可以补充你的业务逻辑，比如刷新数据、初始化页面等
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
				// 非字符串直接返回false
				if (typeof content !== 'string') return false;
				// 去除首尾空格
				const pureContent = content.trim();
				// 空值校验
				if (!pureContent) return false;
				// 纯数字校验
				const numberReg = /^\d+$/;
				if (!numberReg.test(pureContent)) return false;
				// 长度校验
				if (pureContent.length < 15) return false;
				// 所有校验通过
				return true;
			},
			
			confiremQueryQrcode() {
				uni.showModal({
					title: '警告', // 对话框标题
					content: '请确认该笔订单由你本人接手，恶意查询将被封禁', // 提示文字
					cancelText: '取消', // 取消按钮文字
					confirmText: '查询', // 确认按钮文字
					success: (res) => {
						if (res.confirm) {
							this.queryQrcode();
						} else if (res.cancel) {
							uni.showToast({
								title: '已取消操作',
								icon: 'none',
								duration: 1500
							});
						}
					}
				});
			},

			/**
			 * 核心逻辑：调用云函数查询二维码
			 */
			async queryQrcode() {
				this.userInfo = store.userInfo;
				// 1. 前置处理：获取并清洗订单号
				const orderNo = this.orderNo.trim();

				// 2. 校验订单号
				if (!orderNo) {
					this.errorMsg = "请输入订单号";
					return;
				}
				if (!this.validateOrderNo(orderNo)) {
					this.errorMsg = "订单号必须为纯数字且长度不低于15位";
					return;
				}

				// 3. 初始化查询状态
				this.loading = true;
				this.errorMsg = "";
				this.qrcodeSrc = "";

				try {
					// 4. 调用云函数（uniCloud官方API）
					const cloudRes = await uniCloud.callFunction({
						name: "queryGroupQrcode", // 云函数名称（需与部署的一致）
						data: {
							orderNo,
							qr_code: "true",
							booster: this.userInfo.nickname
						} // 传递给云函数的参数
					});

					// 5. 解析云函数返回结果
					const {
						code,
						data,
						msg
					} = cloudRes.result;

					// 6. 新增：boosterInfo权限校验逻辑
					if (code === 200) {
						// 先判断data是否为数组且有数据
						if (Array.isArray(data) && data.length > 0) {

							//之后加判断打手的逻辑
							// const boosterInfo = data[0].bound.booster || "";
							// console.log(boosterInfo);

							if (data[0].join_qr_code) {
								this.qrcodeSrc = data[0].join_qr_code; // 设置二维码地址
								this.errorMsg = "二维码绑定成功，截图后使用微信扫码进群11";

							} else {
								this.errorMsg = "未查询到该订单对应的二维码，联系售后客服";
							}
						}

					} else {
						// code非200，使用云函数返回的错误信息
						this.errorMsg = msg || "系统接口错误，请稍后重试";
					}

				} catch (error) {
					// 7. 异常捕获（网络错误/云函数异常等）
					this.errorMsg = `查询失败：${error.message || "系统异常，请稍后重试"}`;
					console.error("查询二维码异常：", error);
				} finally {
					// 8. 结束加载状态（无论成功/失败）
					this.loading = false;
				}
			}
		}
	};
</script>

<style lang="scss" scoped>
	// 页面全局样式
	.qrcode-query-page {
		padding: 20rpx;
		min-height: 100vh;
		background-color: #f5f5f5;
		box-sizing: border-box;
	}

	// 顶部查询区域
	.query-header {
		background-color: #fff;
		padding: 20rpx;
		border-radius: 12rpx;
		margin-bottom: 20rpx;
		box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.05);

		.input-group {
			display: flex;
			align-items: center;
			gap: 15rpx;

			.order-input {
				flex: 1;
				height: 80rpx;
				line-height: 80rpx;
				padding: 0 20rpx;
				border: 1px solid #e5e5e5;
				border-radius: 8rpx;
				font-size: 28rpx;

				// 优化输入框样式
				&:focus {
					border-color: #007aff;
					outline: none;
				}
			}

			.input-placeholder {
				color: #999;
				font-size: 26rpx;
			}

			.query-btn {
				width: 150rpx;
				height: 80rpx;
				line-height: 80rpx;
				background-color: #007aff;
				color: #fff;
				border: none;
				border-radius: 8rpx;
				font-size: 28rpx;

				&:disabled {
					background-color: #ccc;
					color: #fff;
				}

				&:active:not(:disabled) {
					background-color: #0066cc;
				}
			}
		}

		.error-tip {
			margin-top: 15rpx;
			color: #ff3b30;
			font-size: 24rpx;
			line-height: 1.5;
		}
	}

	// 底部内容容器
	.content-container {
		display: flex;
		flex-direction: column;
		gap: 20rpx;
	}

	// 二维码卡片
	.qrcode-card {
		background-color: #fff;
		padding: 30rpx;
		border-radius: 12rpx;
		text-align: center;
		box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.05);

		.empty-state,
		.loading-state {
			color: #999;
			font-size: 28rpx;
			padding: 100rpx 0;
		}

		.qrcode-img {
			max-width: 100%;
			max-height: 600rpx;
			margin: 0 auto;
			border-radius: 8rpx;
		}
	}

	// 注意事项卡片
	.notice-card {
		background-color: #fff8e1;
		padding: 25rpx;
		border-radius: 12rpx;
		border-left: 6rpx solid #ff9800;
		box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.05);

		.notice-title {
			display: block;
			font-size: 26rpx;
			color: #e65100;
			font-weight: 600;
			margin-bottom: 15rpx;
		}

		.notice-content {
			font-size: 24rpx;
			color: #666;
			line-height: 1.6;
			text-align: justify;
		}
	}
</style>