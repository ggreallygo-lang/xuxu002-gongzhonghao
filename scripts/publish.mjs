// 上传图片 + 建草稿 + 回读核对。不会群发。
import { readFile } from 'node:fs/promises';
import { extname, isAbsolute, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { wechatPublisher } from '@wenyan-md/core/wrapper';

const ROOT = resolve(fileURLToPath(import.meta.url), '../..');

function readEnv(text) {
  return Object.fromEntries(text.split(/\r?\n/).filter(l => l && !l.startsWith('#') && l.includes('='))
    .map(l => { const i = l.indexOf('='); return [l.slice(0, i).trim(), l.slice(i + 1).trim()]; }));
}

const env = readEnv(await readFile(join(ROOT, '.env'), 'utf8'));
const cfg = JSON.parse(await readFile(join(ROOT, 'config.json'), 'utf8'));
const content_ = JSON.parse(await readFile(join(ROOT, 'content.json'), 'utf8'));

const typeOf = (p) => {
  const e = extname(p).toLowerCase();
  return e === '.jpg' || e === '.jpeg' ? 'image/jpeg' : e === '.gif' ? 'image/gif' : 'image/png';
};

function localPath(src) {
  const s = decodeURIComponent(src.replace('file:///', ''));
  return isAbsolute(s) ? s : join(ROOT, s);
}

let html = await readFile(join(ROOT, cfg.article || 'article.html'), 'utf8');
const srcs = [...new Set([...html.matchAll(/<img[^>]+src="([^"]+)"/g)].map(m => m[1]))]
  .filter(s => !s.startsWith('http'));

console.log(`本地图片 ${srcs.length} 张，开始上传`);
const token = await wechatPublisher.getAccessTokenWithCache(env.WECHAT_APP_ID, env.WECHAT_APP_SECRET);

let i = 0;
for (const src of srcs) {
  const p = localPath(src);
  const data = await readFile(p);
  const name = p.split(/[\/]/).pop();
  const r = await wechatPublisher.uploadImage(new File([data], name, { type: typeOf(p) }), name, token, env.WECHAT_APP_ID);
  html = html.split(src).join(r.url);
  console.log(`上传 ${++i}/${srcs.length}：${name}`);
}

const coverPath = join(ROOT, cfg.cover_wide);
const coverData = await readFile(coverPath);
const cover = await wechatPublisher.uploadImage(new File([coverData], 'cover.jpg', { type: 'image/jpeg' }), 'cover.jpg', token, env.WECHAT_APP_ID);

const res = await wechatPublisher.publishToDraft(token, {
  title: content_.title,
  digest: content_.digest || '',
  author: content_.author || '',
  content: html,
  thumb_media_id: cover.media_id,
  content_source_url: '',
  need_open_comment: 0,
  only_fans_can_comment: 0,
});
console.log(`草稿已创建：${res.media_id}`);

// 回读核对
const back = await fetch(`https://api.weixin.qq.com/cgi-bin/draft/get?access_token=${token}`, {
  method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ media_id: res.media_id }),
}).then(r => r.json());
const item = back.news_item?.[0];
if (!item) {
  console.log('回读失败：', JSON.stringify(back));
  process.exit(1);
}
const c = item.content;
console.log('回读：', item.title, '| 图', (c.match(/<img /g) || []).length, '| 表格', (c.match(/<table/g) || []).length);
console.log('封面：', item.thumb_url ? '已设置' : '缺失');
console.log('群发键请自己在后台按。');
