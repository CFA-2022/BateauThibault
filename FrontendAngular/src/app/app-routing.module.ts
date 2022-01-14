import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { DetailsProductComponent } from './pages/details-product/details-product.component';
import { HistoricalDataComponent } from './pages/historical-data/historical-data.component';
import { HomeComponent } from './pages/home/home.component';
import { LoginComponent } from './pages/login/login.component';
import { ManageStockComponent } from './pages/manage-stock/manage-stock.component';

const routes: Routes = [ 
  { path: 'login', component: LoginComponent},
  { path: '', component: HomeComponent },
  { path: 'detail', component: DetailsProductComponent},
  { path: 'stock', component: ManageStockComponent},
  { path: 'data', component: HistoricalDataComponent}
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
