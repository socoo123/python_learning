# Ch23 · 记忆闪卡 & 复习

> Ultralearning 原则七·记忆留存。**先回忆,再翻答案**。连续 2 次秒答 → 退役 ✅。

## 🔖 闪卡

| # | 正面(问题) | 背面(答案) | 掌握 |
|---|---|---|---|
| 1 | 为什么用 pathlib 不用 os.path?`Path / "x"` 是什么操作? | pathlib 把路径变对象,链式调用。`/` 是重载了 `__truediv__` 运算符拼路径(= `Paths.get().resolve()`),不用关心分隔符 | ⬜ |
| 2 | `iterdir`/`glob`/`rglob` 区别?为什么 glob("*") 会列出子目录? | iterdir=遍历顶层;glob(pattern)=顶层通配;rglob=递归通配。三者都把【目录】当条目列出,要文件必须 `if p.is_file()` 过滤 | ⬜ |
| 3 | `Path.stat()` 拿什么?怎么取字节数? | stat() 返回 os.stat_result(inode 信息)。`.st_size`=字节数,`.st_mtime`=修改时间戳。= Java BasicFileAttributes | ⬜ |
| 4 | 幂等建目录(= mkdir -p)怎么写? | `path.mkdir(parents=True, exist_ok=True)`。parents=True 连父目录一起建;exist_ok=True 已存在不报错。= Files.createDirectories | ⬜ |
| 5 | `shutil.move(src, dst)` 最大的坑? | dst【已存在目录】→ 移进去(正常);dst【不存在】→ 把 src【重命名】成 dst 那个文件名(反直觉!)。所以移动到目录前务必先 mkdir | ⬜ |
| 6 | shutil 的 copy2/copytree/rmtree/make_archive 各对应什么 shell? | copy2=cp -p(保留元数据);copytree=cp -r;move=mv;rmtree=rm -rf;make_archive=tar/zip | ⬜ |
| 7 | `Path("a.tar.gz").suffix` 是什么?要全部后缀用什么? | suffix 只取最后一个点后 = ".gz"。要全部 [".tar",".gz"] 用 `.suffixes`。无扩展名 suffix == "" | ⬜ |
| 8 | 递归求目录所有文件总大小,一行怎么写? | `sum(p.stat().st_size for p in directory.rglob("*") if p.is_file())`。rglob 惰性,大目录不爆内存 | ⬜ |

## 🎓 费曼自检

- [ ] 能说清「pathlib vs os.path,`/` 运算符拼路径」?
- [ ] 能说清「glob/iterdir 会列子目录,要 is_file 过滤」?
- [ ] 能说清「shutil.move 目标不存在的重命名陷阱」?

## 📅 复习日程

- [ ] +1 天　日期:________
- [ ] +3 天　日期:________
- [ ] +7 天　日期:________

> 到期登记到根 [`REVIEW.md`](../../REVIEW.md)。
