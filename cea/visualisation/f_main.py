class CEAFrontEnd:
    """Main interface to handle user input, data processing, visualization, and export."""

    def __init__(self, user_input):
        self.user_input = user_input

    def run(self):
        """Executes the full process and returns the Plotly figure."""

        # 1. Process user input
        input_processor = InputProcessor(self.user_input)
        csv_path = input_processor.get_csv_path()
        if not csv_path:
            print("Error: CSV file not found!")
            return None

        # 2. Load data
        loader = CSVLoader(csv_path)
        data = loader.load_data()
        if data is None:
            print("Error: Could not load CSV!")
            return None

        # 3. Process data
        processor = DataProcessor(data)
        processed_data = processor.process_data()

        # 4. Generate plot
        plot_manager = PlotManager(processed_data)
        fig = plot_manager.generate_graph()

        # 5. Provide export options
        exporter = Exporter(processed_data, fig)
        exporter.export_csv("output.csv")
        exporter.export_image("output.png")

        return fig  # Return Plotly figure for frontend
