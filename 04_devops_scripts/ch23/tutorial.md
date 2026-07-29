# Ch23 · 文件系统批量操作:pathlib / shutil

> **预计**:0.5 天 ｜ **前置**:Ch06(with/文件IO)、Ch02(dict)｜ **M4 开篇**
> **目标**:掌握 Python 运维脚本的头号武器——`pathlib`(现代路径 API)+ `shutil`(复制/移动/删目录)。写完这章你能写出「扫文件 → 归类 → 归档」这种批处理脚本,而且代码比 Java 的 `File`/`Files` 短一半。

> 📐 **本教程的契约**:§23.2–§23.5 全部对应作业(6 个函数)。§23.6(日志归档器实战)是综合串联,讲透不出独立题。

---

## 🗺️ 本章地图

**作业 ↔ 教程对应表**:

| 作业 | 对应小节 | 核心知识点 |
|------|----------|-----------|
| `list_files` | §23.2 | pathlib: glob 匹配 + is_file 过滤 + sorted |
| `file_size_report` | §23.2 | iterdir 遍历 + stat().st_size + 字典推导 |
| `group_by_extension` | §23.3 | Path.suffix + setdefault 分组 |
| `ensure_dir` | §23.4 | mkdir(parents=True, exist_ok=True) = `mkdir -p` |
| `total_size` | §23.4 | rglob 递归 + 生成器求和 |
| `archive_files` | §23.5 | shutil.move + 「先建目录」陷阱 |

---

## ⏱️ 学习路径:费曼五步(约 50 分钟)

① 预览猜 → ② 写 assignment(6 个函数)→ ③ pytest 红绿 → ④ 费曼讲清 → ⑤ 存闪卡。

---

## ① 预览猜(先想,别急着翻答案)

1. Java 里拼路径要写 `Paths.get("a", "b", "c.txt")` 或担心 `\` vs `/`。Python 怎么拼?为什么说「用 `/` 运算符拼路径」是 Pythonic?
2. Java 列目录用 `File.listFiles()` 或 `Files.list(path)`。Python 的 `Path.iterdir()` / `glob()` 返回什么?是 `List` 吗?
3. `mkdir -p`(不存在就建、存在不报错)在 Python 怎么一行写出来?
4. 「把一堆日志文件移到 archive 目录」——`shutil.move(f, dst)`,如果 `dst` 不存在会发生什么**反直觉**的事?
5. 递归求一个目录所有文件总大小,Python 一行怎么写?(Java 要 `Files.walk` + stream reduce)

---

## §23.1 为什么用 pathlib 不用 os.path 🟡

Python 老代码里到处是 `os.path.join`、`os.path.exists`、`os.path.getsize`——一串**函数**,操作路径要先把 Path 变字符串传来传去,丑且易错。

`pathlib`(3.4+ 标准库)把路径变成**对象**,链式调用,面向对象:

```python
from pathlib import Path

# 拼路径:用 / 运算符!(Java 老手第一眼会愣,然后真香)
p = Path("/tmp") / "logs" / "app.log"      # == Path("/tmp/logs/app.log")
# 等价于 os.path.join("/tmp", "logs", "app.log"),但不用关心分隔符

p.name        # "app.log"      文件名(含扩展)
p.stem        # "app"          文件名(不含扩展)
p.suffix      # ".log"         扩展名(含点)
p.parent      # Path("/tmp/logs")   父目录
p.exists()    # True/False
p.is_file()   # 是文件吗
p.is_dir()    # 是目录吗
p.read_text(encoding="utf-8")   # 一行读完整个文件(小文件用)
p.write_text("hi", encoding="utf-8")
```

> 🟡 **Java 对比**:`Path` ≈ `java.nio.file.Path`,`/` 运算符 ≈ `Paths.get(...).resolve(...)`。Python 把 `resolve` 简化成了 `/`,这是它最讨人喜欢的语法糖之一。
>
> 🔴 **Python 特有的「真香」**:`Path / "x"` 用除号拼路径。第一次见会很奇怪——除号怎么能拼字符串?因为 `Path` 类重载了 `__truediv__` 运算符(Ch05 魔术方法)。这是运算符重载让 API 更优雅的典范。

**结论**:新代码一律 `pathlib`,别碰 `os.path`(老项目维护才用)。

---

## §23.2 pathlib 基础:遍历与匹配(对应:`list_files`、`file_size_report`)🟢

### 列目录:`iterdir` / `glob` / `rglob`

```python
from pathlib import Path

d = Path("/var/log")

# 1) 遍历顶层条目(含文件和子目录)= Java File.listFiles()
for entry in d.iterdir():
    print(entry)

# 2) 通配符匹配(非递归)= Java Files.newDirectoryStream("*.log")
for p in d.glob("*.log"):        # 只匹配顶层
    print(p)

# 3) 递归匹配
for p in d.rglob("*.log"):       # 递归进所有子目录
    print(p)
```

**关键**:`glob("*")` 和 `iterdir()` 都会**把子目录也列出来**(目录也是「条目」)。要只要文件,得 `if p.is_file()` 过滤。这是新手第一个坑。

> 🟢 **Java 对比**:`iterdir` ≈ `Files.list`,`glob` ≈ `Files.newDirectoryStream(glob)`,`rglob` ≈ `Files.walk` 后过滤。

### 文件元信息:`stat()`

```python
p = Path("app.log")
info = p.stat()           # os.stat_result(= Linux inode 信息)
info.st_size              # 字节数
info.st_mtime             # 修改时间(时间戳秒数)
```

### 作业实现要点

`list_files`:glob 匹配 → is_file 过滤 → 排序。
```python
def list_files(directory: Path, pattern: str = "*") -> list[Path]:
    return sorted((p for p in directory.glob(pattern) if p.is_file()), key=lambda x: x.name)
```
- 为什么 `sorted`?文件系统返回顺序**不保证**(不同 OS、不同文件系统顺序不同),排序让结果稳定、可测。用 `key=lambda x: x.name` 按文件名排(Path 本身也能比,但按 name 更直观)。

`file_size_report`:iterdir + 字典推导。
```python
def file_size_report(directory: Path) -> dict[str, int]:
    return {p.name: p.stat().st_size for p in directory.iterdir() if p.is_file()}
```
- 字典推导(Ch02 学过),一行把 {名字: 大小} 建好。

> ✅ 做 `list_files`:`sorted(...glob(pattern)... if is_file, key=name)`。
> 做 `file_size_report`:`{p.name: p.stat().st_size for p in iterdir() if is_file}`。

---

## §23.3 分组:`Path.suffix` + setdefault(对应:`group_by_extension`)🟡

按扩展名分组文件,运维常见(统计各类日志有多少)。

```python
p = Path("app.log")
p.suffix    # ".log"     含点
Path("readme").suffix    # ""         无扩展名是空串
Path("archive.tar.gz").suffix    # ".gz"   只取最后一个点后
```

分组用 **setdefault**(Ch02 dict 那章讲过,= Java `map.computeIfAbsent`):

```python
def group_by_extension(directory: Path) -> dict[str, list[str]]:
    groups: dict[str, list[str]] = {}
    for p in sorted(directory.iterdir(), key=lambda x: x.name):
        if p.is_file():
            groups.setdefault(p.suffix, []).append(p.name)
    return groups
```

- `groups.setdefault(key, []).append(...)`:key 不存在就先放个空 list,再 append。比 Java 的 `if (!map.containsKey) map.put(k, new ArrayList<>())` 优雅得多。
- 无扩展名文件 → `suffix == ""` → 归到 `""` 键下。

> ✅ 做 `group_by_extension`:`setdefault(p.suffix, []).append(p.name)`,只取 `is_file`。

---

## §23.4 建目录与递归(对应:`ensure_dir`、`total_size`)🟢

### `ensure_dir` = `mkdir -p`

运维脚本第一步常常是「确保输出目录存在」。

```python
def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path
```

两个参数都很关键:
- `parents=True`:连同父目录一起建。`Path("/a/b/c").mkdir()` 默认 `parents=False`,如果 `/a/b` 不存在会报 `FileNotFoundError`。`parents=True` 等于 `mkdir -p`。
- `exist_ok=True`:目录已存在不报错。默认 `exist_ok=False`,已存在会抛 `FileExistsError`。

> 🟢 **Java 对比**:= `Files.createDirectories(path)`(它本身就幂等)。Python 这里反而参数更细,记住 `parents=True, exist_ok=True` 这个组合就是「幂等建目录」。

### `total_size`:递归求和

`rglob("*")` 递归遍历所有条目,生成器 + sum 一行搞定:

```python
def total_size(directory: Path) -> int:
    return sum(p.stat().st_size for p in directory.rglob("*") if p.is_file())
```

对比 Java:
```java
// Java:Files.walk + filter + mapToLong + sum,至少 4 步链
long total = Files.walk(dir)
    .filter(Files::isRegularFile)
    .mapToLong(p -> p.toFile().length())
    .sum();
```
Python 一行,且 `rglob` 是惰性的(生成器),大目录不会一次性全读进内存。

> ✅ 做 `ensure_dir`:`mkdir(parents=True, exist_ok=True)` + `return path`。
> 做 `total_size`:`sum(p.stat().st_size for p in rglob("*") if is_file)`。

---

## §23.5 shutil:复制/移动/删目录(对应:`archive_files`)🔴

`pathlib` 管「路径元信息」,真要**搬动文件**得靠 `shutil`(shell utility,= shell 命令的 Python 版)。

| shutil 函数 | 作用 | shell 等价 |
|-------------|------|-----------|
| `shutil.copy2(src, dst)` | 复制文件(保留元数据) | `cp -p` |
| `shutil.copytree(src, dst)` | 递归复制整棵目录树 | `cp -r` |
| `shutil.move(src, dst)` | 移动/重命名 | `mv` |
| `shutil.rmtree(path)` | 递归删除整棵目录树 | `rm -rf` |
| `shutil.make_archive(...)` | 打包压缩(zip/tar) | `tar/zip` |

> 🟡 **Java 对比**:`shutil.move` ≈ `Files.move`,`shutil.rmtree` ≈ 递归 `Files.walkFileTree` + delete(Java 删目录树很啰嗦,Python 一行)。

### `archive_files` 与「先建目录」陷阱 🔴

```python
def archive_files(files: list[Path], archive_dir: Path) -> int:
    archive_dir.mkdir(parents=True, exist_ok=True)   # ⚠️ 必须先建!
    count = 0
    for f in files:
        shutil.move(str(f), str(archive_dir))
        count += 1
    return count
```

**最大的坑**:`shutil.move(src, dst)` 的行为随 `dst` 而变:
- `dst` 是**已存在的目录** → 把 `src` **移进**该目录(变成 `dst/src.name`)。✅ 这是我们想要的。
- `dst` **不存在** → 把 `src` **重命名成** `dst`(变成一个叫 `dst` 的**文件**!)。❌ 反直觉。

所以**务必先 `mkdir` 建 archive_dir**,否则第一个文件会被重命名成 `archive_dir` 这个文件名,后续全乱套。

> ✅ 做 `archive_files`:先 `archive_dir.mkdir(parents=True, exist_ok=True)`,再循环 `shutil.move(str(f), str(archive_dir))` 计数。`str()` 是因为 shutil 接受字符串路径(新版本也接受 Path,但 str 最稳)。

---

## §23.6 实战:日志归档器(6 个函数串起来,讲透不出题)

把这章的零件组装成真实运维脚本:「扫描某目录,按扩展名分组报告,把超过阈值的文件移到归档目录」。

```python
from pathlib import Path
import shutil

def archive_large_logs(log_dir: Path, archive: Path, threshold: int) -> dict:
    """把 log_dir 下大于 threshold 字节的文件归档,返回报告。"""
    ensure_dir(archive)                                   # §23.4 先建归档目录

    report = file_size_report(log_dir)                    # §23.2 拿到大小
    to_archive = [
        log_dir / name for name, size in report.items()
        if size >= threshold                              # 超阈值的
    ]
    moved = archive_files(to_archive, archive)            # §23.5 移走

    return {
        "scanned": len(report),
        "archived": moved,
        "remaining_by_ext": group_by_extension(log_dir),  # §23.3 剩余文件归类
        "archive_total_bytes": total_size(archive),       # §23.4 归档目录总大小
    }

# 跑起来
if __name__ == "__main__":
    print(archive_large_logs(Path("/var/log/myapp"), Path("/backup/logs"), 10_000_000))
```

看,6 个函数像积木一样拼成真实工具——这就是「小函数 + 组合」的 Pythonic 风格(Java 老手熟悉,但 Python 写起来更短)。

---

## §23.7 Java 老手常踩的坑 ⚠️

1. **忘 `is_file()` 过滤**:`glob("*")` 和 `iterdir()` 会把**子目录**也列出来。要文件必须 `if p.is_file()`。
2. **`shutil.move` 目标不存在**:不报错,而是**重命名**成那个名字的文件。移动到目录前务必 `mkdir`。
3. **`mkdir` 不加参数**:默认 `parents=False, exist_ok=False`——中间目录缺了报错、目录已存在也报错。运维脚本要 `mkdir(parents=True, exist_ok=True)`。
4. **用 `os.path` 拼字符串**:新代码别这么写,`pathlib` 的 `/` 运算符和链式方法优雅得多。
5. **`p.read_text()` 读大文件**:`read_text` 一次读全文件进内存。GB 级日志要用 `open(p) ` 逐行(Ch03 生成器)或 `mmap`。
6. **`suffix` vs `suffixes`**:`Path("a.tar.gz").suffix == ".gz"`(只最后一个),要 `[".tar", ".gz"]` 用 `.suffixes`。

---

## 📝 本章作业

| 任务 | 知识点 | 难度 |
|------|--------|------|
| `list_files` | glob + is_file + sorted | 🟢 |
| `file_size_report` | iterdir + stat + 字典推导 | 🟢 |
| `group_by_extension` | suffix + setdefault 分组 | 🟡 |
| `ensure_dir` | mkdir(parents, exist_ok) | 🟢 |
| `total_size` | rglob 递归 + sum | 🟢 |
| `archive_files` | shutil.move + 先建目录陷阱 | 🔴 |

```bash
uv run pytest 04_devops_scripts/ch23/test_ch23_assignment.py -v
```

全绿 = 掌握 Ch23。

---

## ✅ 自测

- [ ] 能用 `Path / "x"` 拼路径,知道为什么用 `/` 运算符(运算符重载)
- [ ] 知道 `glob`/`iterdir` 会列出子目录,要文件得 `is_file()` 过滤
- [ ] 会写幂等建目录 `mkdir(parents=True, exist_ok=True)`(= `mkdir -p`)
- [ ] 能说清 `shutil.move` 在「目标不存在」时的反直觉行为
- [ ] 6 个作业全绿

## 🎓 费曼挑战

1. 「同样是列目录,`iterdir`、`glob`、`rglob` 有什么区别?为什么 `glob("*")` 还会列出子目录?」— 重读 §23.2
2. 「`shutil.move(f, archive)` 如果 `archive` 目录还没建,会发生什么?为什么必须先 `mkdir`?」— 重读 §23.5
3. 「`pathlib.Path` 重载了哪个魔术方法,让 `/` 能拼路径?」— 重读 §23.1(回 Ch05 魔术方法)

## 🧠 记忆闪卡 → [`review.md`](./review.md)

---

## ⏭️ 下一步:Ch24 进程与子进程

文件会搬了,接下来学「**调用外部命令 + 监控系统进程**」——`subprocess`(= Java `ProcessBuilder`)+ `psutil`(跨平台系统监控)。运维脚本第二大场景。
