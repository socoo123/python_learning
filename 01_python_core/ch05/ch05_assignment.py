"""
Ch05 作业:OOP —— 魔术方法、继承、dataclass。

场景:你是电商后台的「领域建模」负责人。今天要把一整套领域类写出来——
商品、订单、库存清单、价目表、金额、折扣购物车、结算台,并且让它们
像 Python 内置类型一样好用:能 len()、能 in、能 for、能 []、能 +、
能 ==、能当字典 key、repr 出来人看得懂。

每题是一个【类工厂】函数:在函数体内定义题目要求的类,然后 return 这个类
(返回类本身,不是实例!)。测试拿到你的类后会做全套质检。
为什么可以这样写?——类也是对象(Ch01):函数可以造类、返回类,
标准库 collections.namedtuple 就是一个官方类工厂。

在每处 TODO 写你的实现,然后:

    uv run pytest 01_python_core/ch05/test_ch05_assignment.py -v

全绿 = 你掌握了 Ch05。

每题 docstring 里标了【对应小节】,卡住 → 回 tutorial.md 查对应 §。
(提示只给思路和关键语法,不给完整代码——自己组合才有掌握感。)
"""
from dataclasses import dataclass


# ========== §5.1 类的基础 + @dataclass ==========


def make_product_class():
    """
    【场景】商品库要一个 Product 模型:名字、单价、库存。Java 里你得写字段 +
    构造器 + getter + equals + hashCode + toString(或祭出 Lombok / record);
    Python 标准库的 @dataclass 一个装饰器全包。

    【转换点】@dataclass 自动生成 __init__ / __repr__ / __eq__。
    规则:带默认值的字段必须排在无默认值字段的后面(和函数默认参数同理)。
    注意本函数返回的是【类本身】:return Product,不加括号!

    任务:在函数体内定义并返回一个 @dataclass 类 Product,字段依次为:
        name: str
        price: float
        stock: int = 0
    示例(测试就是这样用你的类的):
        Product = make_product_class()
        Product("机械键盘", 599.0, 10).name        -> "机械键盘"
        Product("无线鼠标", 159.0).stock           -> 0      (默认值生效)
        Product("A", 1.0, 2) == Product("A", 1.0, 2) -> True (自动 __eq__)
        repr(Product("机械键盘", 599.0, 10))
            -> "...Product(name='机械键盘', price=599.0, stock=10)"  (自动 __repr__)

    提示:
        @dataclass
        class Product:
            name: str
            price: float
            stock: int = 0
        return Product      # 返回类,不加括号
        (类定义在函数内,repr 会带 make_product_class.<locals> 前缀,正常现象)
    """
    # TODO: @dataclass + class Product(三个字段,注意顺序) + return Product
    ...


# ========== §5.2 @property:把计算伪装成字段 ==========


def make_order_class():
    """
    【场景】订单 Order:明细项是 dict {"name", "price", "qty"}。后台结算页
    要看订单总金额——希望像访问字段一样写 order.total,而不是 order.get_total()。

    【转换点】@property 把方法包装成「只读属性」:外部像字段一样访问(不带括号!),
    内部实际是每次现算。没定义 setter → 赋值会抛 AttributeError(天然只读)。
    ⚠️ 实例属性必须在 __init__ 里用 self.xxx 创建;写在类体里的是【类属性】,
    所有实例共享同一个(≈ Java static),测试会专门拦这个坑。

    任务:在函数体内定义并返回类 Order:
        __init__(self):初始化空明细列表 self._items(list[dict])
        add_item(self, name, price, qty=1):追加 {"name": name, "price": price, "qty": qty}
        @property total:总金额 = Σ price × qty,round(..., 2);空订单为 0
        (total 只读:不要定义 setter)
    示例:
        Order = make_order_class()
        o = Order()
        o.add_item("机械键盘", 599.0, 2)
        o.add_item("无线鼠标", 159.0)        # qty 默认 1
        o.total         -> 1357.0            (599.0×2 + 159.0×1,像字段一样访问!)
        Order().total   -> 0
        o.total = 999   -> AttributeError    (没定义 setter → 只读)

    提示:
        class Order:
            def __init__(self):
                self._items = []          # 实例属性,不是类属性!
            @property
            def total(self):
                return round(sum(... 用生成式遍历 self._items ...), 2)
        return Order
    """
    # TODO: class Order(__init__ / add_item / @property total) + return Order
    ...


# ========== §5.3 容器协议:len / in / for / [] ==========


def make_inventory_class():
    """
    【场景】库存清单 Inventory:sku → 库存数。仓管要做三件事:看清单里有几种
    SKU(len)、判断某个 SKU 在不在清单里(in)、遍历所有 SKU 打印盘点表(for)。

    【转换点】容器协议三件套:__len__ → len(inv);__contains__ → sku in inv;
    __iter__ → for sku in inv。Java 里这是 size() / contains() / implements
    Iterable 三件各自为政的事,Python 是统一协议——这就是「鸭子类型」的地基。
    ⚠️ 构造时把传进来的字典【拷一份】(dict(stock)),否则外部改原字典会
    影响清单(≈ Java 的 new HashMap<>(m) 防御性拷贝),测试会拦。

    任务:在函数体内定义并返回类 Inventory:
        __init__(self, stock: dict):保存 {sku: qty},拷一份
        __len__(self):SKU 种数
        __contains__(self, sku):"KB-001" in inv
        __iter__(self):按插入顺序遍历 sku
    示例:
        Inventory = make_inventory_class()
        inv = Inventory({"KB-001": 120, "MS-002": 300})
        len(inv)          -> 2
        "KB-001" in inv   -> True
        "XX-000" in inv   -> False
        list(inv)         -> ["KB-001", "MS-002"]   (按插入顺序)

    提示:
        class Inventory:
            def __init__(self, stock):
                self._stock = dict(stock)     # 防御性拷贝
            def __iter__(self):
                return iter(self._stock)      # 直接复用 dict 的迭代器
        return Inventory
    """
    # TODO: class Inventory(__init__ 拷贝 / __len__ / __contains__ / __iter__)
    ...


def make_price_list_class():
    """
    【场景】价目表 PriceList:给 sku 查价格。调用方希望像字典一样写
    price_list["KB-001"],而不是 price_list.get_by_sku("KB-001")。

    【转换点】__getitem__ 让自定义类支持 [] 语法(= Java 的 get(i),但接进了
    语言级的索引语法)。sku 不存在时要抛 KeyError——直接用字典取值就行,
    字典对不存在的 key 天然抛 KeyError,不用自己判断。

    任务:在函数体内定义并返回类 PriceList:
        __init__(self, prices: dict):保存 {sku: price},拷一份
        __getitem__(self, sku):返回价格;sku 不存在抛 KeyError
    示例:
        PriceList = make_price_list_class()
        pl = PriceList({"KB-001": 599.0, "MS-002": 159.0})
        pl["KB-001"]   -> 599.0      (像字典一样用 [] 取值)
        pl["NOPE"]     -> 抛 KeyError

    提示:
        class PriceList:
            def __getitem__(self, sku):
                return self._prices[sku]   # dict 对缺失 key 天然抛 KeyError
        return PriceList
    """
    # TODO: class PriceList(__init__ 拷贝 / __getitem__)
    ...


# ========== §5.4 运算符与显示:__add__ / __eq__ / __hash__ / __repr__ ==========


def make_money_class():
    """
    【场景】财务对账:金额 Money 要支持相加凑单(Money(100) + Money(50))、
    判等对账(==)、当字典 key 做「按金额聚合计数」、打印出来财务看得懂。

    【转换点】四条契约,条条对应 Java 老手的老朋友:
      · __add__:返回【新】Money,绝不改 self/other(Java 没有运算符重载,
        BigInteger 只能 a.add(b);Python 任何类都能定义 + 的含义)
      · __eq__:判等前先 isinstance 检查,不认识的类型返回 NotImplemented
        (不是抛异常!Python 会再试对方的反向方法,都不行才抛 TypeError)
      · __hash__:一定义 __eq__,__hash__ 就自动变 None(实例不可哈希,
        set/dict key 全废)——≈ Java「重写 equals 必须重写 hashCode」,
        Python 直接把 hashCode 没收逼你重写。要和 __eq__ 保持一致
      · __repr__:给程序/调试看的官方表示,目标「无歧义」
    (真实账务请用 Decimal,本章用 float 简化,别拿 0.1+0.2 这种值较真)

    任务:在函数体内定义并返回类 Money:
        __init__(self, amount: float):存公开的 self.amount
        __add__(self, other):返回新 Money;非 Money 返回 NotImplemented
        __eq__(self, other):同类型且金额相等;非 Money 返回 NotImplemented
        __hash__(self):hash(self.amount)
        __repr__(self):f"Money({self.amount:.2f})"  (:.2f = 两位小数)
    示例:
        Money = make_money_class()
        (Money(100.0) + Money(50.0)).amount  -> 150.0   (新对象,原来的不变)
        Money(12.5) == Money(12.5)           -> True
        Money(1.0) == 1.0                    -> False   (类型不同,不抛异常)
        len({Money(10.0), Money(10.0)})      -> 1       (__eq__+__hash__ 一致 → 可去重)
        repr(Money(12.5))                    -> "Money(12.50)"
        Money(1.0) + 5                       -> TypeError(NotImplemented 的连锁反应)

    提示:
        def __eq__(self, other):
            if not isinstance(other, Money):
                return NotImplemented
            return self.amount == other.amount
        (类在方法里可以直接引用自己的名字 Money——方法被调用时类已定义好)
    """
    # TODO: class Money(__init__ / __add__ / __eq__ / __hash__ / __repr__)
    ...


# ========== §5.5 继承与 super() ==========


def make_discount_cart_class():
    """
    【场景】大促折扣车:和普通购物车一样能加商品、算总价,但结算时整单打折。
    普通车的逻辑已经写好了,折扣车【复用】它,只改总价算法——这就是继承的活。

    【转换点】class 子类(父类): ≈ Java extends(没有 @Override 注解,同名即覆盖)。
    super() ≈ Java super:super().__init__() 先初始化父类部分;
    子类覆盖父类的 @property 时,super().total 能拿到父类 property 的值,
    实现「复用父类计算 + 加自己的逻辑」。
    本题要求父类 Cart 也定义在本函数体内(自包含,方便单独质检)。

    任务:在函数体内依次定义两个类,返回【子类】:
        1) 父类 Cart:
             __init__(self):self._items = []
             add(self, name, price):追加 {"name": name, "price": price}
             @property total:Σ price(不用 round)
        2) 子类 DiscountedCart(Cart):
             __init__(self, discount=0.1):先 super().__init__(),再存 self.discount
             覆盖 @property total:round(super().total * (1 - self.discount), 2)
        3) return DiscountedCart     (返回子类,不是父类!)
    示例:
        DC = make_discount_cart_class()
        c = DC(discount=0.2)
        c.add("机械键盘", 599.0)     # add 是从父类继承的
        c.add("无线鼠标", 159.0)
        c.total            -> 606.4   (758.0 × (1 - 0.2))
        DC().discount      -> 0.1     (默认 9 折)
        DC.__mro__[1].__name__ -> "Cart"   (真的继承了函数内的 Cart)

    提示:
        class Cart: ...父类三件套...
        class DiscountedCart(Cart):
            @property
            def total(self):
                return round(super().total * (1 - self.discount), 2)
        return DiscountedCart
    """
    # TODO: class Cart + class DiscountedCart(Cart) + return DiscountedCart
    ...


# ========== §5.6 综合实战:结算台 Checkout ==========


def make_checkout_class():
    """
    【场景】收银台的结算台 Checkout:把本章的魔法一次性用全——加商品、
    len 看件数、in 查商品、for 打明细、+ 合并两台结算单、total 算金额、
    repr 打小票头。这是本章毕业题。

    【转换点】一个类里集成全部协议时,类内部也可以用【自己的】魔术方法:
    __repr__ 里直接写 len(self) 和 self.total,不用重复实现。

    任务:在函数体内定义并返回类 Checkout(明细项是 dict {"name","price","qty"}):
        __init__(self):self._items = []
        add(self, name, price, qty=1):追加明细
        __len__(self):总件数 = Σ qty(注意:不是明细条数!)
        __contains__(self, name):按商品名查,"机械键盘" in c
        __iter__(self):遍历明细 dict
        __add__(self, other):合并两台 → 【新】Checkout(明细拼接),不改原来两台
        @property total:Σ price × qty,round(..., 2)
        __repr__(self):f"Checkout({明细条数} 种商品, 共 {总件数} 件, ¥{total})"
            —— 逗号是半角加空格 ", ";金额直接插值(如 ¥1357.0,空的为 ¥0)
    示例:
        Checkout = make_checkout_class()
        c = Checkout()
        c.add("机械键盘", 599.0, 2)
        c.add("无线鼠标", 159.0)              # qty 默认 1
        len(c)                 -> 3           (2 + 1)
        "机械键盘" in c         -> True
        [i["name"] for i in c] -> ["机械键盘", "无线鼠标"]
        c.total                -> 1357.0
        repr(c)  -> "Checkout(2 种商品, 共 3 件, ¥1357.0)"
        repr(Checkout()) -> "Checkout(0 种商品, 共 0 件, ¥0)"
        merged = c + Checkout()   # 新对象;len(c) 仍为 3,合并不改原件

    提示:
        __len__ 里 sum(i["qty"] for i in self._items);
        __add__ 里 new = Checkout(); new._items = self._items + other._items;
        __repr__ 里用 len(self._items)(种数)、len(self)(件数)、self.total。
    """
    # TODO: class Checkout(__init__/add/__len__/__contains__/__iter__/__add__/total/__repr__)
    ...


# ---------------------------------------------------------------------
# 实现完后可直接运行本文件看效果(不是测试,测试请用 pytest):
#     uv run python 01_python_core/ch05/ch05_assignment.py
# ---------------------------------------------------------------------
if __name__ == "__main__":
    Product = make_product_class()
    kb = Product("机械键盘", 599.0, 120)
    print("dataclass 自动 repr:", repr(kb))
    print("自动 __eq__:", kb == Product("机械键盘", 599.0, 120))

    Order = make_order_class()
    o = Order()
    o.add_item("机械键盘", 599.0, 2)
    o.add_item("无线鼠标", 159.0)
    print("订单总价(@property):", o.total)

    Inventory = make_inventory_class()
    inv = Inventory({"KB-001": 120, "MS-002": 300})
    print("库存 SKU 种数:", len(inv), "| KB-001 在吗:", "KB-001" in inv)

    PriceList = make_price_list_class()
    pl = PriceList({"KB-001": 599.0})
    print("价目表查价:", pl["KB-001"])

    Money = make_money_class()
    print("金额相加:", Money(100.0) + Money(50.0), "| set 去重:", len({Money(10.0), Money(10.0)}))

    DC = make_discount_cart_class()
    dc = DC(discount=0.2)
    dc.add("机械键盘", 599.0)
    dc.add("无线鼠标", 159.0)
    print("8 折结算:", dc.total)

    Checkout = make_checkout_class()
    c = Checkout()
    c.add("机械键盘", 599.0, 2)
    c.add("无线鼠标", 159.0)
    print("结算台小票头:", repr(c))
