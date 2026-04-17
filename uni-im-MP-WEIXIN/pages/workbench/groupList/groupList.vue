<template>
	<view class="contacts-groupList">
		<uni-search-bar placeholder="搜索群号/群名称" :radius="100" bgColor="#eeeeee" v-model="keyword" @cancel="doClear"
			@clear="doClear"></uni-search-bar>
		<view class="uni-list">
			<uni-im-info-card v-for="(item,index) in groupList" :key="index" @click="toChat(item._id)" link
				:title="item?.name" :avatar="item?.avatar_file?.url || '/uni_modules/uni-im/static/avatarUrl.png'">
			</uni-im-info-card>
			<uni-im-load-state class="uni-im-load-state" :status="groupHasMore?'loading':'noMore'"></uni-im-load-state>
		</view>
	</view>
</template>

<script>
	import uniIm from '@/uni_modules/uni-im/sdk/index.js';
	export default {
		data() {
			return {
				keyword: '',
				groupData: false
			}
		},
		computed: {
			//是否为pc宽屏（width>960px）
			isWidescreen() {
				return uniIm.isWidescreen
			},
			groupList() {
				const groupList = uniIm.group.dataList
				if (this.keyword) {
					return groupList.filter(item => {
						return item.name.includes(this.keyword) || item._id.includes(this.keyword)
					})
				} else {
					return groupList
				}
			},
			groupHasMore() {
				return uniIm.group.hasMore
			}
		},
		mounted() {
			const onIntersect = (res) => {
				if (res.intersectionRatio > 0) {
					uniIm.group.loadMore()
				}
			}
			// 微信小程序：传 Vue 的 this 会触发「enumerating keys on component instance」警告，且默认走慢路径
			// 应传 this.$scope（原生页面/组件实例）并开启 nativeMode
			// #ifdef MP-WEIXIN
			uni.createIntersectionObserver(this.$scope, { nativeMode: true })
				.relativeToViewport({ bottom: 0 })
				.observe('.uni-im-load-state', onIntersect)
			// #endif
			// #ifndef MP-WEIXIN
			const io = uni.createIntersectionObserver(this)
			// #ifdef H5
			io.relativeTo('body', {})
			// #endif
			// #ifndef H5
			io.relativeToViewport({ bottom: 0 })
			// #endif
			io.observe('.uni-im-load-state', onIntersect)
			// #endif
		},
		onShow() {
			// 观察器未就绪或未触发时兜底拉一页（与 imData.init 并行无害，CloudData 内有 loading 队列）
			if (uniIm.group.hasMore && uniIm.group.dataList.length === 0) {
				uniIm.group.loadMore()
			}
		},
		async onLoad(options) {
			this.setParam(options)
		},
		methods: {
			setParam(param = {}) {
				if (param.group_id) {
					this.keyword = param.group_id
				}
			},
			doClear() {
				this.keyword = ''
			},
			toChat(group_id) {
				let conversation_id = 'group_' + group_id
				uniIm.toChat({
					conversation_id
				})
			}
		}
	}
</script>

<style lang="scss">
	@import "@/uni_modules/uni-im/common/baseStyle.scss";

	.contacts-groupList {

		/* #ifdef H5 */
		@media screen and (min-device-width:960px) {
			.uni-list {
				height: calc(100vh - 165px);
				overflow: auto;
			}
		}

		/* #endif */
	}
</style>