import csv
import os

class CSVwritter:
    """
    Classe permettant d'enregistrer des donnees dans un fichier CSV
    """

    def __init__(self, p_columns : list[str], p_save_dir : str, p_file_name : str = None):
        """
        p_columns : list[str] : nom des colonnes du CSV
        p_save_dir : str : repertoire ou sera sauvegarde le fichier CSV
        p_file_name : str : nom du fichier (optionnel)
        !!! si un fichier est deja existant sous le meme nom donne, alors le fichier sera overwritte
        """

        self.__file_name = p_file_name
        self.__directory = p_save_dir
        if self.__file_name == None:
            self.__file_name = self.getFileName( self.__directory )

        print( f"Ouverture du fichier {self.__directory+self.__file_name}" )

        self.__f = open(
            self.__directory+self.__file_name,
            'w',
            newline=''
        )

        # objet writer pour ecrire dans le fichier CSV
        self.writer = csv.writer(self.__f)

        self.__n_columns = len( p_columns )
        self.writeColumn( p_columns )

    def writeColumn(self, p_data:list):
        """
        Écrit une entrée dans le fichier CSV
        p_data : list : La liste des données a enregistrer
        Retourne True si l'écriture a réussi, False sinon
        """

        if self.writer is None:
            return False

        if len(p_data) != self.__n_columns:
            return False
        
        self.writer.writerow(p_data)
        return True

    def closeCSVWriter(self):
        """
        Ferme le fichier CSV
        """

        if self.writer is None:
            return
        
        self.__f.close()
        print("CSV file has been closed")
        return

    def getFileName(self, p_dir : str) -> str:
        """
        Trouve le nom du fichier où les données seront sauvegardées
        p_dir : str : Le chemin où les données seront sauvegardées
        Retourne le nom du fichier, ou None si le chemin n'est pas valide
        """
        
        try:
            os.chdir(p_dir)
        except Exception as e:
            raise Exception("Le chemin pour sauvegarder le données n'est pas valide")

        # chercher index du dernier fichier enregistre
        i = 0
        r_file_name = f"Arduino_recording_{i}.csv"
        while os.path.exists( r_file_name ):
            i += 1
            r_file_name = f"Arduino_recording_{i}.csv"

        return r_file_name

if __name__=="__main__":
    colonnes = ["temps", "valeur"]
    repertoire = "./"
    fichier = "test.csv"

    wcsv = CSVwritter( colonnes, repertoire, fichier )

    for i in range(10):
        wcsv.writeColumn( [i, i] )

    wcsv.closeCSVWriter()