
import tkinter as tk
from tkinter import messagebox, ttk

from PIL import Image, ImageTk

from billboard import *
from city import *


class App():
    """ Class App where the root of the app is set."""

    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.protocol('WM_DELETE_WINDOW', self.close)
        self.root.resizable(0, 0)
        self.root.title("CineBus")

        self.billboard = Billboard()
        build_and_save_graphs()
        self.buses_graph = load_graph('buses.grf')
        self.osmnx_graph = load_graph('osmnx.grf')
        self.city_graph = load_graph('barcelona.grf')

        self.frame = StartPage(self.root)
        self.frame.pack()

    def change(self, frame) -> None:
        """Changes the visible frame, keeping the same root."""
        self.frame.pack_forget()
        self.frame = frame(self.root)
        self.frame.pack()

    def hide(self) -> None:
        """Hides root."""
        self.root.withdraw()

    def show(self) -> None:
        """Shows root."""
        self.root.update()
        self.root.deiconify()

    def close(self) -> None:
        """Closes application."""
        self.root.destroy()


class StartPage(tk.Frame):  # the frame inherits atributes from general Frame
    """Class StartPage. First page of the app."""

    def __init__(self, root) -> None:
        tk.Frame.__init__(self, root)

        tk.Label(self, text='Cinebus', fg='#03989E', font=('Source Sans Pro', 24, 'bold')).grid(
            columnspan=3, row=0, column=1, padx=10, pady=10)

        tk.Label(self, text='Fet per:', font=('Source Sans Pro', 12, 'bold')).grid(
            columnspan=3, row=1, column=1, padx=10, pady=2)

        tk.Label(self, text='Gerard Grau i Pol Resina', font=(
            'Source Sans Pro', 12, 'bold')).grid(columnspan=3, row=2, column=1, padx=10, pady=2)

        tk.Button(self, command=self.siguiente_page, text='Endevant', cursor='hand2').grid(
            row=3, column=3, padx=10, pady=10, sticky='e')

    def siguiente_page(self) -> None:
        """Changes the visible page to PageOne."""
        app.change(PageOne)


class PageOne(tk.Frame):  # the frame inherits atributes from general Frame
    """Class PageOne. Page of the app where we can select one from the 3 options."""

    def __init__(self, root) -> None:
        """Constructor of the class PageOne, where all tkinter configurations are set."""

        tk.Frame.__init__(self, root)

        tk.Button(self, command=self.PageBillboard,  text='Cartellera', font=('Source Sans Pro', 10, 'bold'),
                  cursor='hand2').grid(columnspan=3, row=0, column=1, padx=10, pady=10)

        tk.Button(self, command=self.PageMapes, text='Veure mapes', font=('Source Sans Pro', 10, 'bold'),
                  cursor='hand2').grid(columnspan=3, row=1, column=1, padx=10, pady=10)

        tk.Button(self, command=self.PageRuta, text='Seleccionar pel·lícula', cursor='hand2', font=('Source Sans Pro', 10, 'bold')
                  ).grid(columnspan=3, row=2, column=1, padx=10, pady=10)

        tk.Button(self, text='Cancel·lar', command=self.startPage, cursor='hand2').grid(
            row=3, column=3, padx=10, pady=10, sticky='e')

    def startPage(self) -> None:
        """Changes the visible page to StartPage, the previous frame."""
        app.change(StartPage)

    def PageBillboard(self) -> None:
        """Changes the visible page to PageBillboard."""
        app.change(PageBillboard)

    def PageMapes(self) -> None:
        """Changes the visible page to PageMapes."""
        app.change(PageMapes)

    def PageRuta(self) -> None:
        """Changes the visible page to PageRuta."""
        app.change(PageRuta)


class PageBillboard(tk.Frame):  # the frame inherits atributes from general Frame
    """Page of the app where we can see the Billboard in an interactive way."""

    def __init__(self, root) -> None:
        tk.Frame.__init__(self, root)

        tk.Label(self, text='Pel·lícules disponibles:', font=(
            'MONOSPACED', 12, 'bold')).grid(row=0, column=0, columnspan=11, pady=(20, 0))

        self.films_tree = ttk.Treeview(self, columns=(
            1, 2, 3, 4, 5, 6), show='headings', selectmode="browse")  # características de la tabla
        self.films_tree.grid(row=1, column=0, columnspan=11, padx=50, pady=15)

        self.films_tree.column(1, anchor=tk.CENTER, width=250)
        self.films_tree.column(2, anchor=tk.CENTER, width=200)
        self.films_tree.column(3, anchor=tk.CENTER, width=180)
        self.films_tree.column(4, anchor=tk.CENTER, width=200)
        self.films_tree.column(5, anchor=tk.CENTER, width=200)
        self.films_tree.column(6, anchor=tk.CENTER, width=250)

        self.films_tree.heading(1, text='Peli', anchor=tk.CENTER)
        self.films_tree.heading(2, text='Cinema', anchor=tk.CENTER)
        self.films_tree.heading(3, text='Inici de la peli', anchor=tk.CENTER)
        self.films_tree.heading(4, text='Gènere', anchor=tk.CENTER)
        self.films_tree.heading(5, text='Directors', anchor=tk.CENTER)
        self.films_tree.heading(6, text='Actors', anchor=tk.CENTER)

        tk.Label(self, text='Cerca pel·lícules:', font=('MONOSPACED', 11, 'bold')).grid(
            row=2, column=0, columnspan=11, pady=5)

        tk.Label(self, text='Peli:').grid(
            row=3, column=0, padx=(50, 0), pady=10)

        self.film_entry = tk.Entry(self)
        self.film_entry.grid(row=3, column=1, pady=10)

        tk.Label(self, text='Cinema:').grid(
            row=3, column=2, padx=(10, 0), pady=10)

        self.cine_entry = tk.Entry(self)
        self.cine_entry.grid(row=3, column=3, pady=10)

        tk.Label(self, text='Gènere:').grid(
            row=3, column=4, padx=(10, 0), pady=10)

        self.genre_entry = tk.Entry(self)
        self.genre_entry.grid(row=3, column=5, pady=10)

        tk.Label(self, text='Director:').grid(
            row=3, column=6, padx=(10, 0), pady=10)
        self.director_entry = tk.Entry(self)
        self.director_entry.grid(row=3, column=7, pady=10)

        tk.Label(self, text='Actor:').grid(
            row=3, column=8, padx=(10, 0), pady=10)

        self.actor_entry = tk.Entry(self)
        self.actor_entry.grid(row=3, column=9, pady=10)

        tk.Button(self, text='Cerca', command=self.search,
                  cursor='hand2').grid(row=3, column=10, padx=50)

        self.search()  # empty parameters, every projection will be shown

        tk.Label(self, text='Cines amb més pel·lícules disponibles:', font=(
            'MONOSPACED', 11, 'bold')).grid(row=4, column=0, columnspan=11, pady=(20, 0))

        self.cinemas_tree = ttk.Treeview(self, columns=(
            1, 2, 3), show='headings', selectmode='browse')
        self.cinemas_tree.grid(
            row=5, column=0, columnspan=11, padx=50, pady=20)

        self.cinemas_tree.column(1, anchor=tk.CENTER, width=250)
        self.cinemas_tree.column(2, anchor=tk.CENTER, width=400)
        self.cinemas_tree.column(3, anchor=tk.CENTER, width=300)

        self.cinemas_tree.heading(1, text='Nom', anchor=tk.CENTER)
        self.cinemas_tree.heading(2, text='Adreça', anchor=tk.CENTER)
        self.cinemas_tree.heading(
            3, text='# Projeccions en menys de 24h', anchor=tk.CENTER)

        cinema_vals = [(cinema.name, cinema.address, len(cinema.get_projections_in_1_day()))
                       for cinema in app.billboard.cinemas]

        for cinema_value in sorted(cinema_vals):
            self.cinemas_tree.insert('', tk.END, value=cinema_value)

        tk.Button(self, text='Cancel·lar', command=self.PageOne, cursor='hand2').grid(
            row=6, column=10, padx=10, pady=10, sticky='e')

    def PageOne(self) -> None:
        """Changes the visible page to PageOne."""
        app.change(PageOne)

    def search(self) -> None:
        """Search projections given initial parameters. If they are all empty it returns all the projections."""

        self.films_tree.delete(*self.films_tree.get_children())

        projections = app.billboard.search_projections(
            self.film_entry.get(), self.cine_entry.get(), self.genre_entry.get(), self.director_entry.get(), self.actor_entry.get())

        projections.sort(key=operator.attrgetter('start_time'))
        projection_values = [(proj.film.title, proj.cinema.name, proj.start_time, ', '.join(proj.film.genres), ', '.join(proj.film.directors), ', '.join(proj.film.actors))
                             for proj in projections]

        for projection_value in projection_values:
            self.films_tree.insert('', tk.END, value=projection_value)


class PageMapes(tk.Frame):  # the frame inherits atributes from general Frame
    """Page of the app where we can see the maps in a tkinter page."""

    def __init__(self, root) -> None:
        tk.Frame.__init__(self, root)

        tk.Button(self, text='Mostrar el graf  de la ciutat', command=self.mostrar_graf_ciutat,
                  cursor='hand2').grid(row=0, column=1, columnspan=3, padx=10, pady=10, sticky='e')
        tk.Button(self, text='Mostrar el graf  de la ciutat', command=self.mostrar_graf_ciutat,
                  cursor='hand2').grid(row=0, column=1, columnspan=3, padx=10, pady=10, sticky='e')
        tk.Button(self, text='Mostrar el graf dels busos', command=self.mostrar_graf_busos,
                  cursor='hand2').grid(row=1, column=1, columnspan=3, padx=10, pady=10, sticky='e')
        tk.Button(self, text='Cancel·lar', command=self.PageOne, cursor='hand2').grid(
            row=2, column=3, padx=10, pady=10, sticky='e')

    def mostrar_graf_busos(self) -> None:
        """Toplevel whose purpose is to show the picture with the graph of the buses."""
        app.hide()
        self.top = tk.Toplevel()
        self.top.protocol('WM_DELETE_WINDOW', self.ask_quit)
        self.top.title('CineBus')

        if not os.path.exists('buses.png'):
            plot(app.buses_graph, 'buses.png')

        image = Image.open('buses.png')
        self.display = ImageTk.PhotoImage(image)
        tk.Label(self.top, image=self.display).grid(row=0, column=0)

    def mostrar_graf_ciutat(self) -> None:
        """Toplevel whose purpose is to show the picture with the graph of barcelona."""
        app.hide()
        self.top = tk.Toplevel()
        self.top.protocol('WM_DELETE_WINDOW', self.ask_quit)
        self.top.title('CineBus')

        if not os.path.exists('barcelona.png'):
            plot(app.city_graph, 'barcelona.png')

        image = Image.open('barcelona.png')
        self.display = ImageTk.PhotoImage(image)
        tk.Label(self.top, image=self.display).grid(row=0, column=0)

    def PageMapes(self) -> None:
        """Changes the visible page to PageMapes."""
        app.change(PageMapes)

    def PageOne(self) -> None:
        """Changes the visible page to PageOne."""
        app.change(PageOne)

    def ask_quit(self) -> None:
        """Changes the visible page to PageOne."""
        self.top.destroy()
        self.top.update()
        app.change(PageMapes)
        app.show()


class PageRuta(tk.Frame):
    """Page of the app where we can select, see and get information about the route to the cinema."""

    def __init__(self, root) -> None:
        tk.Frame.__init__(self, root)

        tk.Label(self, text='Busca la pel·lícula', font=('Source Sans Pro', 12)).grid(
            columnspan=3, row=0, column=1, padx=10, pady=(20, 0))
        self.film_entry = tk.Entry(self)
        self.film_entry.grid(columnspan=8, row=1, column=0, padx=10, pady=10)

        tk.Label(self, text='Introdueix coordenades:', font=('Source Sans Pro', 12)).grid(
            columnspan=3, row=2, column=1, padx=10, pady=(20, 0))

        tk.Label(self, text='Latitud (y)', font=('Source Sans Pro', 12)).grid(
            row=3, column=0, padx=(20, 1), pady=10)
        self.srcy = tk.Entry(self)
        self.srcy.grid(columnspan=3, row=3, column=1, padx=10, pady=10)

        tk.Label(self, text='Longitud (x)', font=('Source Sans Pro', 12)).grid(
            row=4, column=0, padx=(20, 5), pady=10)
        self.srcx = tk.Entry(self)
        self.srcx.grid(columnspan=3, row=4, column=1, padx=10, pady=10)

        tk.Button(self, text='Crear ruta', command=self.selecciopeli, cursor='hand2').grid(
            row=5, column=3, padx=10, pady=10, sticky='e')
        tk.Button(self, text='Cancel·lar', command=self.PageOne, cursor='hand2').grid(
            row=5, column=4, padx=10, pady=10, sticky='e')

    def selecciopeli(self) -> None:
        """Toplevel whose purpose is to show the available films, given the title introduced."""

        if not app.billboard.search_film_title(self.film_entry.get()):
            messagebox.showwarning(
                "Error", "No hi ha cap pel·lícula disponible amb aquest nom! Potser t'has equivocat escrivint el nom.")
            return None

        def is_not_float(s): return not s.replace('.', '').isnumeric()
        if is_not_float(self.srcx.get()) or is_not_float(self.srcy.get()):
            messagebox.showwarning(
                "Error", "Has de posar un format vàlid a les coordenades. Per exemple:\n41.2345\n2.123345")
            return None

        app.hide()

        self.top = tk.Toplevel()
        self.top.protocol('WM_DELETE_WINDOW', self.ask_quit)

        self.top.title('CineBus')

        self.films_tree = ttk.Treeview(self.top, columns=(
            1), show='headings', selectmode='browse')  # características de la tabla
        self.films_tree.grid(row=0, column=0, columnspan=3,
                             padx=(10, 10), pady=(15, 20))

        self.films_tree.column(1, anchor=tk.CENTER, width=300)

        self.films_tree.heading(1, text='Pelis', anchor=tk.CENTER)

        self.title = self.film_entry.get()
        self.nom_pelis = {
            peli.title: peli for peli in app.billboard.search_film_title(self.title)}

        for title in self.nom_pelis:
            self.films_tree.insert('', 'end', values=[title])

        self.button = tk.Button(
            self.top, text='Veure projeccions', command=self.seleccioprojeccio, cursor='hand2')
        self.button.grid(row=1, column=1, padx=10, pady=10)

    def seleccioprojeccio(self) -> None:
        """Toplevel whose purpose is to show the available projections given the film selected."""

        nom = self.films_tree.item(self.films_tree.selection())['values'][0]
        self.peli = self.nom_pelis[nom]
        self.src = Coord(self.srcx.get(), self.srcy.get())

        self.top.destroy()
        self.top.update()

        self.top = tk.Toplevel()
        self.top.protocol('WM_DELETE_WINDOW', self.ask_quit)
        self.top.title('CineBus')

        self.path_to_cinemas: dict[str, Path] = {}

        def dona_temps_a_arribar(src: Coord, projection: Projection) -> bool:
            """Retorna si dona temps a arribar des de la coordenada fins al cinema de la projecció."""
            if projection.cinema.name not in self.path_to_cinemas:
                self.path_to_cinemas[projection.cinema.name] = find_path(
                    app.osmnx_graph, app.city_graph, src, projection.cinema.loc)
            return dt.datetime.now() + self.path_to_cinemas[projection.cinema.name].duration < projection.start_time

        tk.Label(self.top, text="Projeccions de " + nom + "\n(a les que pots arribar a temps)",
                 font=('Source Sans Pro', 12, 'bold')).grid(row=0, column=0, columnspan=3, padx=10, pady=10)

        self.projections_tree = ttk.Treeview(self.top, columns=(
            1, 2), show='headings', selectmode='browse')  # características de la tabla
        self.projections_tree.grid(
            row=1, column=0, columnspan=3, padx=10, pady=10)

        self.projections_tree.column(1, anchor=tk.CENTER, width=250)
        self.projections_tree.column(2, anchor=tk.CENTER, width=250)

        self.projections_tree.heading(1, text='Cinema', anchor=tk.CENTER)
        self.projections_tree.heading(2, text='Horari', anchor=tk.CENTER)

        print("S'estan obtenint les projeccions a les que et dona temps a arribar...")
        self.projections = sorted(
            self.peli.projections, key=operator.attrgetter('start_time'))
        for projection in self.projections:
            if dona_temps_a_arribar(self.src, projection):
                self.projections_tree.insert('', 'end', values=(
                    projection.cinema.name, projection.start_time))

        tk.Button(self.top, text='Crear ruta', command=self.ShowRuta,
                  cursor='hand2').grid(row=2, column=1, padx=10, pady=10)

    def ShowRuta(self) -> None:
        """Toplevel whose purpose is to show the picture with the route to the cinema in order to see the film selected."""

        nom_cine, hora_inici = self.projections_tree.item(
            self.projections_tree.selection())['values']
        self.projeccio = [proj for proj in self.projections if proj.cinema.name ==
                          nom_cine and str(proj.start_time) == hora_inici][0]

        self.top.destroy()
        self.top.update()

        self.top = tk.Toplevel()
        self.top.protocol('WM_DELETE_WINDOW', self.ask_quit)
        self.top.title('CineBus')

        print("S'està creant la ruta fins al cinema " + nom_cine + "...")
        path = self.path_to_cinemas[nom_cine]

        plot_path(app.city_graph, path, 'path_graph.png')

        image = Image.open('path_graph.png')
        self.display = ImageTk.PhotoImage(image)
        tk.Label(self.top, image=self.display).grid(
            row=0, column=0, columnspan=2)

        tk.Button(self.top, text='Veure ruta de tornada', command=self.ShowRutaTornada,
                  cursor='hand2').grid(row=1, column=0, padx=80, pady=10, sticky='w')
        tk.Button(self.top, text='Cancel·lar', command=self.ask_quit, cursor='hand2').grid(
            row=1, column=1, padx=100, pady=10, sticky='e')

        path_message = obtenir_indicacions(
            app.city_graph, path, nom_cine, self.projeccio.start_time, self.projeccio.end_time)
        print('\n\n' + "Indicacions:" + '\n\n' + path_message + '\n')
        messagebox.showinfo('Indicacions:', path_message)

    def ShowRutaTornada(self) -> None:
        """Toplevel used to plot the graph of the return path"""
        self.top.destroy()
        self.top.update()

        self.top = tk.Toplevel()
        self.top.protocol('WM_DELETE_WINDOW', self.ask_quit)
        self.top.title('CineBus')

        path = find_path(app.osmnx_graph, app.city_graph,
                         self.projeccio.cinema.loc, self.src)
        plot_path(app.city_graph, path, 'path_graph_tornada.png')

        image = Image.open('path_graph_tornada.png')
        self.display = ImageTk.PhotoImage(image)
        tk.Label(self.top, image=self.display).grid(row=0, column=0)
        tk.Button(self.top, text='Cancel·lar', command=self.ask_quit, cursor='hand2').grid(
            row=1, column=0, padx=100, pady=10, sticky='se')

        path_message = obtenir_indicacions(
            app.city_graph, path, hora_fi=self.projeccio.end_time, anada=False)
        print('\n' + "Indicacions de tornada:" + '\n\n' + path_message + '\n')
        messagebox.showinfo('Indicacions de tornada:', path_message)

    def PageOne(self) -> None:
        """Changes the visible page to PageOne."""
        app.change(PageOne)

    def ask_quit(self) -> None:
        """Quits Toplevel and changes to PageOne."""
        self.top.destroy()
        self.top.update()
        app.change(PageOne)
        app.show()


if __name__ == '__main__':
    print("S'està iniciant l'aplicació...")
    app = App()
    app.root.mainloop()
