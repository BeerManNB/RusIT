import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns


df_a = pd.read_csv(r'Приложение A', delimiter='\t')
df_b = pd.read_csv(r'Приложение B', delimiter='\t')
df_c = pd.read_csv(r'Приложение C', delimiter='\t')


project_sum_hours    = df_a['Часы'].sum()
project_mean_hours   = df_a['Часы'].mean()
project_median_hours = df_a['Часы'].median()

print('1. Общие трудозатраты на проект в часах:', project_sum_hours)
print('2. Среднее время, затраченное на решение задач в часах -', round(project_mean_hours,1))
print('3. Медианное время, затраченное на решение задач в часах -', project_median_hours,'\n')


# тут двойная группировка, некоторые задачи разбиты на 2 дня.
# сначала собираются задачи по дням, потом среднее по работникам
# в датафрейме person_df будут хранится данные в разрезе работников

person_df = df_a.groupby(['Исполнитель', 'Задача']).agg({'Часы':'sum'}) \
                .groupby('Исполнитель').agg({'Часы':'mean'}) \
                .reset_index() \
                .rename(columns={'Часы':'mean_hours','Исполнитель':'person'})
person_df['mean_hours'] = round(person_df['mean_hours'], 1)

print('4. Среднее время, затраченное на решение задач каждым из исполнителей в часах:', '\n', person_df, '\n')

# всё в person_df пусть лежит в 1ом месте. часы, оплата за час, общая зарплата
person_df['total_hours']  = df_a.groupby('Исполнитель').agg({'Часы':'sum'}).reset_index()['Часы']
person_df['pay_per_hour'] = df_c['Ставка']
person_df['salary']       = person_df.total_hours * person_df.pay_per_hour


revenue = 24000
profit = revenue - person_df['salary'].sum()
rentability = profit / revenue * 100
print('5. Рентабельность проекта -', round(rentability, 1),'\n' )


person_df['work_days'] = df_a.groupby(['Исполнитель']).agg({'Дата':'nunique'}).reset_index()['Дата']
person_df['mean_hour_per_day'] = round(person_df.total_hours / person_df.work_days, 1)
print('6. Среднее количество часов, отрабатываемое каждым сотрудником за день', '\n', person_df.loc[:,['person', 'mean_hour_per_day']], '\n')

# перевожу в datetime формат, отмечаю выходные.
# создаю date_range от первого до последнего дня в датафрейме
# складываю всё в множества ( люблю множества, они математичны) и смотрю их разность.

df_a['Дата'] = pd.to_datetime(df_a['Дата'],format = '%d.%m.%Y')
df_a['is_weekend'] = np.where((df_a['Дата'].dt.dayofweek) < 5,0,1)
work_period = pd.date_range(start = df_a['Дата'].min(), end = df_a['Дата'].max())
work_period = set(filter(lambda x: x.dayofweek < 5, work_period))
person_df['person_work_days'] = df_a.query('is_weekend == 0') \
                                    .groupby('Исполнитель') \
                                    .agg({'Дата':'unique'}) \
                                    .reset_index()['Дата']
person_df['lose_days'] = person_df['person_work_days'].apply(lambda x: work_period - set(pd.to_datetime(x)) )
person_df['lose_days'] = person_df['lose_days']
print('7. Дни отсутствия для каждого сотрудника', '\n', person_df.loc[:,['person', 'lose_days']], '\n')


# merge "оценка" и "часы" по задаче.
# объединяю задачи разбитые на несколько дней
# считаю проценты. положительные проценты - задержка, отрицательные - быстрее срока
df_proc         = df_b.merge(df_a, how='inner', on='Задача')[['Задача','Оценка','Исполнитель','Часы']]
df_proc         = df_proc.groupby(['Задача','Оценка','Исполнитель']).agg({'Часы':'sum'}).reset_index()
df_proc['proc'] = (df_proc['Часы'] / df_proc['Оценка'] - 1 )*100
person_df['mean_procent_delay'] = df_proc.groupby('Исполнитель').agg({'proc':'mean'}).reset_index().proc
person_df['mean_procent_delay'] = round(person_df['mean_procent_delay'],1)

print('8. Средний «вылет» специалиста из оценки в процентах', '\n', person_df.loc[:, ['person', 'mean_procent_delay']], '\n')


# собираю df для барплота с двойными столбцами. и строю его
df_barplot = df_proc.loc[:,['Задача','Оценка','Часы']].sort_values('Задача')
df_barplot = df_barplot.set_index('Задача')
df_barplot = df_barplot.stack().reset_index().rename({'Задача':'Task','level_1':'legend',0:'hours'},axis = 1)
df_barplot = df_barplot.sort_values('hours',ascending = False)

plt.figure(figsize=(10,14))
plt.grid()
ax = sns.barplot(data = df_barplot, x='hours' , y='Task', hue='legend')
plt.savefig('hop_hey_lalaley.png')

