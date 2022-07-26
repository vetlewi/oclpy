import oclpy as ocl


if __name__ == '__main__':
	cal = ocl.ReadCalDGF('test.list')
	print(cal[(0,0)])