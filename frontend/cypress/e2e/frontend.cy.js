describe("Frontend IMV", () => {

  it("Carga la página principal", () => {
    cy.visit("/");
    cy.contains("Simulación de carga digital en IMV");
  });

  it("Carga la tabla de pacientes", () => {
    cy.visit("/");
    cy.contains("Pacientes recibidos");
    cy.get("#patients-table tbody tr").should("exist");
  });

  // it("Permite lanzar una simulación", () => {
  //   cy.visit("/");
  //   cy.get("#num_generators").clear().type("1");
  //   cy.get("#patients_per_generator").clear().type("10");
  //   cy.contains("Iniciar simulación").click();
  //   cy.contains("Simulación lanzada").should("exist");
  // });

});
