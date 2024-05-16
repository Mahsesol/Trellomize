import npyscreen

class MyForm(npyscreen.Form):
    def create(self):
        self.add(npyscreen.TitleText, name="Text1:", value="Window 1")
        self.add(npyscreen.TitleText, name="Text2:", value="Window 2")
        self.add(npyscreen.TitleText, name="Text3:", value="Window 3")

class MyApplication(npyscreen.NPSAppManaged):
    def onStart(self):
        self.addForm("MAIN", MyForm, name="Window 1")
        self.addForm("SECONDARY", MyForm, name="Window 2")
        self.addForm("TERTIARY", MyForm, name="Window 3")

if __name__ == "__main__":
    app = MyApplication().run()
