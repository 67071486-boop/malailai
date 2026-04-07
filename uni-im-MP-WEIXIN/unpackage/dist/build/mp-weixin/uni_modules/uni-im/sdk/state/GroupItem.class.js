"use strict";const r=require("./GroupMember.class.js");exports.GroupItem=class{constructor(e){for(let r in e)this[r]=e[r];this.member=new r.GroupMember({group_id:this._id})}};
