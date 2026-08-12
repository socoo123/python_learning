# Ch23 · 记忆闪卡 & 复习

> Ultralearning 原则七·记忆留存。**先回忆,再翻答案**。连续 2 次秒答 → 退役 ✅。

## 🔖 闪卡

| # | 正面(问题) | 背面(答案) | 掌握 |
|---|---|---|---|
| 1 | 为什么用 pathlib 不用 os.path?`Path / "x"` 是什么操作? | pathlib 把路径变对象,链式调用。`/` 是重载了 `__truediv__` 运算符拼路径(≈ `Paths.get`+`resolve`),不用关心分隔符 | ⬜ |
| 2 | `iterdir` / `glob` / `rglob` 区别?为什么遍历结果必须过滤? | iterdir=顶层全部条目;glob(p)=顶层通配;rglob(p)=递归通配。三者都把【目录】当条目返回,要文件必须 `if p.is_file()` | ⬜ |
| 3 | 为什么 `list_files` 要 `sorted`? | 文件系统返回顺序不保证(因 OS/文件系统而异),排序让结果稳定、可测 | ⬜ |
| 4 | `Path.stat()` 拿什么?字节数哪个字段? | stat() 返回 os.stat_result(inode 信息 ≈ Java BasicFileAttributes)。`.st_size`=字节数,`.st_mtime`=修改时间戳 | ⬜ |
| 5 | `Path("app.1.log").suffix` 和 `.suffixes` 各是什么?无扩展名呢? | suffix 只取最后一个点后=".log";suffixes=[".1",".log"]。无扩展名 suffix == ""(空串,不是 None) | ⬜ |
| 6 | dict 分组时 `setdefault(k, [])` 等价于 Java 什么? | `map.computeIfAbsent(k, x -> new ArrayList<>())`:key 不存在先放空 list 并返回,存在返回现有 list,之后安全 append | ⬜ |
| 7 | 幂等建目录(= mkdir -p)怎么写?两个参数各防什么? | `path.mkdir(parents=True, exist_ok=True)`。parents 防「中间目录不存在」(FileNotFoundError);exist_ok 防「目录已存在」(FileExistsError)。= Files.createDirectories | ⬜ |
| 8 | `exist_ok=True` 时,同名【文件】已存在会怎样? | 照样抛 FileExistsError——它只对「已存在的是目录」宽容。同名文件是配置错误,早暴露为好 | ⬜ |
| 9 | 🔴 `shutil.move(src, dst)` 最大的坑? | dst 是【已存在目录】→ 移进去(正常);dst【不存在】→ 把 src【重命名】成 dst 那个文件名(变文件!)。移动到目录前务必先 mkdir | ⬜ |
| 10 | shutil 的 copy2 / copytree / move / rmtree / make_archive 各对应什么 shell? | copy2=`cp -p`;copytree=`cp -r`;move=`mv`;rmtree=`rm -rf`;make_archive=`tar`/`zip` | ⬜ |
| 11 | `with_name` / `with_suffix` 会改磁盘上的文件吗? | 不会,只返回新 Path 对象。真正改名要 `p.rename(新路径)`(= os.rename,同文件系统原子) | ⬜ |
| 12 | 原地改名用 `rename` 还是 `shutil.move`?为什么? | 原地改名用 `p.rename()`(同文件系统原子操作);搬到别的目录/跨设备用 `shutil.move`(底层先 copy 再删,且目标是目录时自动移进去) | ⬜ |
| 13 | 递归求目录所有文件总大小,一行怎么写? | `sum(p.stat().st_size for p in directory.rglob("*") if p.is_file())`。rglob 返回惰性生成器,大目录不爆内存 | ⬜ |
| 14 | `archive_large_logs` 为什么必须「先 file_size_report → 再 archive_files → 最后 group_by_extension」? | 报告要的是「归档前扫到多少、归档后剩什么」。顺序反了,remaining_by_ext 会把已搬走的文件也算进去 | ⬜ |

## 🎓 费曼自检

- [ ] 能说清「pathlib vs os.path,`/` 运算符拼路径(`__truediv__`)」?
- [ ] 能说清「glob/iterdir 会列子目录,要 is_file 过滤;顺序不保证要 sorted」?
- [ ] 能说清「shutil.move 目标不存在的重命名陷阱 + 先建目录」?
- [ ] 能说清「with_name 只算不动、rename 才落盘;rename vs shutil.move 怎么选」?

## 📅 复习日程

- [ ] +1 天　日期:________
- [ ] +3 天　日期:________
- [ ] +7 天　日期:________

> 到期登记到根 [`REVIEW.md`](../../REVIEW.md)。
