



class Fibonacci:

    def __init__(self, nterms: int):
        self.nterms = nterms

    def recur_fib(self, n: int):
        if n <= 1:
            return n
        else:
            return self.recur_fib(n-1) + self.recur_fib(n-2)

    def output(self):
        for i in range(self.nterms):
            print(self.recur_fib(i))






if __name__ == "__main__":
    myFib = Fibonacci(10)
    myFib.output()