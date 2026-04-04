from dataclasses import dataclass
@dataclass
class T:
    a: int



def func(obj:T):
    obj.a=3
def func2(obj:int):
    obj=3

if __name__ == '__main__':
    t = T(1)
    func(t)
    print(t.a)

    a=1
    func2(a)
    print(a)